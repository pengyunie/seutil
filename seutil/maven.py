import dataclasses
import functools
import os
from pathlib import Path
from typing import List, Set

import xmltodict

import seutil as su

logger = su.log.get_logger(__name__, su.log.INFO)

SKIPS = "-Djacoco.skip -Dcheckstyle.skip -Drat.skip -Denforcer.skip -Danimal.sniffer.skip -Dmaven.javadoc.skip -Dfindbugs.skip -Dwarbucks.skip -Dmodernizer.skip -Dimpsort.skip -Dpmd.skip -Dxjc.skip -Dair.check.skip-all"


@dataclasses.dataclass
class MavenModule:
    group_id: str
    artifact_id: str
    version: str
    packaging: str
    rel_path: str = "."
    project: "MavenProject" = None
    pom_modified: Set[str] = dataclasses.field(default_factory=set)

    def serialize(self):
        return {
            "group_id": self.group_id,
            "artifact_id": self.artifact_id,
            "version": self.version,
            "packaging": self.packaging,
            "rel_path": self.rel_path,
        }

    @functools.cached_property
    def main_srcpath(self) -> str:
        return str(self.project.dir / self.rel_path / "src" / "main" / "java")

    @functools.cached_property
    def test_srcpath(self) -> str:
        return str(self.project.dir / self.rel_path / "src" / "test" / "java")

    @functools.cached_property
    def main_classpath(self) -> str:
        return str(self.project.dir / self.rel_path / "target" / "classes")

    @functools.cached_property
    def test_classpath(self) -> str:
        return str(self.project.dir / self.rel_path / "target" / "test-classes")

    @functools.cached_property
    def dependency_classpath(self) -> str:
        with su.io.cd(self.project.dir / self.rel_path):
            tmp_file = su.io.mktmp(prefix="cp")
            su.bash.run(
                f"mvn dependency:build-classpath -Dmdep.outputFile={tmp_file}", 0
            )
            classpath = su.io.load(tmp_file, fmt=su.io.Fmt.txt)
            su.io.rm(tmp_file)
            return classpath

    @functools.cached_property
    def exec_classpath(self) -> str:
        with su.io.cd(self.project.dir / self.rel_path):
            tmp_file = su.io.mktmp(prefix="ecp")
            su.bash.run(
                f"mvn -q exec:exec -Dexec.executable=echo -Dexec.args='%classpath' > {tmp_file}",
                0,
            )
            classpath = su.io.load(tmp_file, fmt=su.io.Fmt.txt).strip()
            su.io.rm(tmp_file)
            return classpath

    @functools.cached_property
    def coordinate(self) -> str:
        return f"{self.group_id}:{self.artifact_id}:{self.version}"

    def backup_pom(self):
        if len(self.pom_modified) > 0:
            raise RuntimeError(
                f"Cannot backup pom.xml for {self.coordinate} because it has been modified"
            )
        with su.io.cd(self.project.dir / self.rel_path):
            su.bash.run("cp pom.xml pom.xml.backup", 0)

    def restore_pom(self):
        with su.io.cd(self.project.dir / self.rel_path):
            su.bash.run("cp pom.xml.backup pom.xml", 0)
        self.pom_modified.clear()

    def hack_pom_delete_plugin(self, artifact_id: str):
        """Hack the pom.xml to delete plugin with the given artifact_id"""
        modification = f"delete_plugin:{artifact_id}"
        if modification in self.pom_modified:
            logger.debug(f"pom.xml for {self.coordinate} already did {modification}")
            return

        pom = xmltodict.parse(
            su.io.load(self.project.dir / self.rel_path / "pom.xml", fmt=su.io.Fmt.txt)
        )

        plugins = pom.get("build", {}).get("plugins", {}).get("plugin", [])
        to_remove = None
        for i, plugin in enumerate(plugins):
            if plugin.get("artifactId") == artifact_id:
                to_remove = i
                break
        if to_remove is not None:
            del plugins[to_remove]

        su.io.dump(
            self.project.dir / self.rel_path / "pom.xml",
            xmltodict.unparse(pom),
            fmt=su.io.Fmt.txt,
        )

        self.pom_modified.add(modification)

    def compile(self, timeout=600, retry_with_package=True, clean=False):
        with su.io.cd(self.dir / self.rel_path):
            if clean:
                su.bash.run("mvn clean", 0)
            rr = su.bash.run(f"mvn test-compile {SKIPS}", timeout=timeout)
            if rr.returncode != 0:
                if retry_with_package:
                    su.bash.run(f"mvn package -DskipTests {SKIPS}", 0, timeout=timeout)
                else:
                    raise RuntimeError(f"Failed to compile")

    @property
    def dir(self) -> Path:
        return self.project.dir / self.rel_path


@dataclasses.dataclass
class MavenProject:
    multi_module: bool = False
    modules: List[MavenModule] = dataclasses.field(default_factory=list)
    dir: Path = None

    def serialize(self):
        return {
            "multi_module": self.multi_module,
            "modules": su.io.serialize(self.modules),
        }

    @classmethod
    def from_project(cls, project: su.project.Project) -> "MavenProject":
        if not (project.dir / "pom.xml").exists():
            return None
        project.require_cloned()
        maven_proj = cls(dir=project.dir)
        # detect modules from the project
        with su.io.cd(maven_proj.dir):
            rr = su.bash.run(
                """mvn -Dexec.executable='bash' -Dexec.args='-c '"'"'echo ${project.groupId}:${project.artifactId}:${project.version} ${project.packaging} ${PWD}'"'"'' exec:exec -q""",
                0,
            )
        for line in rr.stdout.splitlines():
            coord, packaging, abs_path = line.split(" ", 2)
            group_id, artifact_id, version = coord.split(":")
            rel_path = str(Path(abs_path).relative_to(maven_proj.dir))
            maven_proj.modules.append(
                MavenModule(
                    group_id=group_id,
                    artifact_id=artifact_id,
                    version=version,
                    packaging=packaging,
                    rel_path=rel_path,
                    project=maven_proj,
                )
            )
            maven_proj.modules.sort(key=lambda m: m.coordinate)
        maven_proj.multi_module = len(maven_proj.modules) > 1
        return maven_proj

    def backup_pom(self):
        for module in self.modules:
            module.backup_pom()

    def restore_pom(self):
        for module in self.modules:
            module.restore_pom()

    def hack_pom_delete_plugin(self, artifact_id: str):
        for module in self.modules:
            module.hack_pom_delete_plugin(artifact_id)

    def compile(self, timeout=600, retry_with_package=True, clean=False):
        with su.io.cd(self.dir):
            if clean:
                su.bash.run("mvn clean", 0)
            rr = su.bash.run(f"mvn test-compile {SKIPS}", timeout=timeout)
            if rr.returncode != 0:
                if retry_with_package:
                    su.bash.run(f"mvn package -DskipTests {SKIPS}", 0, timeout=timeout)
                else:
                    raise RuntimeError(f"Failed to compile")

    def install(self, timeout=600, clean=False):
        with su.io.cd(self.dir):
            if clean:
                su.bash.run("mvn clean", 0)
            rr = su.bash.run(f"mvn install -DskipTests {SKIPS}", 0, timeout=timeout)
            if rr.returncode != 0:
                raise RuntimeError(f"Failed to install")

    def get_module_by_path(self, file_path: Path) -> MavenModule:
        module_path = file_path.parent
        while module_path != Path("."):
            if (module_path / "src/main/java").exists() or (
                module_path / "src/test/java"
            ).exists():
                break
            module_path = module_path.parent
        for module in self.modules:
            if os.path.realpath(module.rel_path) == os.path.realpath(module_path):
                return module
        raise RuntimeError(f"Failed to find module for {file_path}, {module_path}")
