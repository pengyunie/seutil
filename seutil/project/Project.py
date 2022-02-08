import shutil
from pathlib import Path
from typing import *

from .. import io, bash, log
from .ProjectResults import ProjectResults


logger = log.get_logger(__name__, log.INFO)


class Project:

    DOWNLOADS_DIR = Path.cwd() / "_downloads"
    RESULTS_DIR = Path.cwd() / "_results"

    @classmethod
    def set_downloads_dir(cls, path: Path):
        cls.DOWNLOADS_DIR = path
        return

    @classmethod
    def set_results_dir(cls, path: Path):
        cls.RESULTS_DIR = path
        return

    def __init__(self):
        self.full_name: str = "UNKNOWN"  # Should always be a valid directory name, i.e., not containing "/", " ", etc.
        self.url: str = ""
        self.checkout_dir: Path = None

        self.data: Dict = dict()

        self.results: ProjectResults = None
        return

    def serialize(self) -> dict:
        jsonfied = dict()
        jsonfied["full_name"] = self.full_name
        jsonfied["url"] = self.url
        for e, v in self.data.items():
            if e in ["full_name", "url"]:
                continue
            else:
                jsonfied[e] = v
        return jsonfied

    @classmethod
    def deserialize(cls, data) -> "Project":
        obj = cls()
        obj.full_name = data["full_name"]
        obj.url = data["url"]
        obj.data.update(data)
        return obj

    def init_results(self, results_dir: Path = None):
        if results_dir is None:
            results_dir = self.default_results_dir

        results = ProjectResults()
        results.full_name = self.full_name
        results.results_dir = results_dir
        self.results = results
        return

    @property
    def is_connected_to_results(self):
        return self.results is not None

    @classmethod
    def from_projects_database(cls, projects_database: List[Dict]) -> List["Project"]:
        projects = list()

        for project_data in projects_database:
            project = Project()
            project.full_name = project_data["full_name"].replace("/", "_")
            project.data = project_data
            project.url = "https://github.com/{}".format(project_data["full_name"])
            projects.append(project)

        return projects

    @property
    def default_checkout_dir(self):
        return Project.DOWNLOADS_DIR / self.full_name

    @property
    def default_results_dir(self):
        return Project.RESULTS_DIR / self.full_name

    @property
    def default_branch(self):
        return self.data.get("default_branch", "HEAD")

    @property
    def logger_prefix(self):
        return "Project {}: ".format(self.full_name)

    @property
    def is_cloned(self):
        return self.checkout_dir is not None

    def clone(self, checkout_dir: Path = None, is_force_update: bool = False):
        """
        Clones the project to path. The project will be checked-out to the default branch, latest revision.
        If the project is already cloned, then will only move the project to the given path, and check out to the default branch, latest revision.
        :param checkout_dir: the location to clone and checkout the project.
        :param is_force_update: if true, then will re-clone regardless of whether the project is cloned before.
        """
        # Get default checkout path
        if checkout_dir is None:
            if self.checkout_dir is not None:
                checkout_dir = self.checkout_dir
            else:
                checkout_dir = self.default_checkout_dir

        # Respect is_force_update
        if is_force_update:
            self.remove()

        checkout_dir.mkdir(parents=True, exist_ok=True)
        if self.checkout_dir is None:
            # Clone, if not done so
            logger.info(self.logger_prefix + f"Cloning to {checkout_dir}")
            with io.cd(checkout_dir):
                bash.run(f"git clone {self.url} .")
        else:
            # Move, if has already cloned version
            logger.info(
                self.logger_prefix
                + f"Already cloned to {self.checkout_dir}, moving to {checkout_dir}"
            )
            shutil.move(str(self.checkout_dir), str(checkout_dir))

        # Update checkout path
        self.checkout_dir = checkout_dir

        # Update repo
        self.update()
        return

    def require_cloned(self) -> None:
        """
        Checks if the project is cloned.
        :raises Exception: if the project is not cloned.
        """
        if not self.is_cloned:
            raise Exception("Project is not cloned")
        return

    def update(self):
        """
        Updates the cloned repo to the latest version of default branch.
        """
        self.require_cloned()

        logger.info(
            self.logger_prefix
            + f"Updating to latest version of branch {self.default_branch}"
        )
        with io.cd(self.checkout_dir):
            self.checkout(self.default_branch, True)
            bash.run("git fetch", check_returncode=0)
            self.checkout(self.default_branch, True)
        return

    def remove(self) -> None:
        """
        Removes the project from local disk if it is cloned. Do nothing otherwise.
        """
        if self.is_cloned:
            logger.info(self.logger_prefix + "Removing")
            shutil.rmtree(self.checkout_dir, ignore_errors=True)
            self.checkout_dir = None
        else:
            logger.info(self.logger_prefix + "Already removed")

    def checkout(self, revision: str, is_forced: bool = False) -> None:
        """
        Checks out to the given revision.
        :requires: the project to be cloned.
        :param revision: the target revision.
        :param is_forced: if do force checkout or not.
        """
        self.require_cloned()

        logger.info(self.logger_prefix + "Checking-out to {}".format(revision))
        with io.cd(self.checkout_dir):
            bash.run(
                f"git checkout {'-f' if is_forced else ''} {revision}",
                check_returncode=0,
            )

    def clean(self) -> None:
        """
        Cleans any extra files in the repository that is not indexed by git (either git-ignored or not).
        :requires: the project to be cloned.
        """
        self.require_cloned()

        logger.info(self.logger_prefix + "Cleaning")
        with io.cd(self.checkout_dir):
            bash.run("git clean -ffdx", check_returncode=0)

    @property
    def revision(self) -> str:
        """
        Returns the current revision of the project.
        :requires: the project to be cloned.
        :return: the current revision of the project.
        """
        self.require_cloned()

        with io.cd(self.checkout_dir):
            revision = bash.run(
                "git log --pretty='%H' -1", check_returncode=0
            ).stdout.strip()
        return revision

    def get_all_revisions(self) -> List[str]:
        """
        Returns the revisions of the history of the current branch, before (and include) the current revision.
        The revisions are sorted in chronological order, i.e., latest revision at last.

        Updates the results with "all_revisions.json".

        :requires: the project to be cloned.
        :return: the list of revisions of current branch history, sorted in chronological order.
        """
        self.require_cloned()

        with io.cd(self.checkout_dir):
            # Revisions in chronological order
            all_revisions = bash.run(
                "git log --pretty='%H'", check_returncode=0
            ).stdout.split("\n")[:-1]
            all_revisions.reverse()
        logger.info(
            self.logger_prefix + "All revisions count: {}".format(len(all_revisions))
        )

        if self.is_connected_to_results:
            self.results.dump_meta_result("all_revisions.json", all_revisions)

        return all_revisions

    def for_each_revision(
        self,
        func_revision: Callable[["Project", str], None],
        revisions: Iterable[str],
        is_auto_checkout: bool = True,
    ) -> None:
        """
        Runs the func_revision for each revision.
        :param func_revision: the function to run, which takes a Project object and a string revision, and is able to access the ProjectResults.
        :param revisions: the revisions to run the function.
        :param is_auto_checkout: if set to False then will not automatically checkout each revision.
        """
        if isinstance(revisions, list):
            revisions_count = len(revisions)
        else:
            revisions_count = "-"

        for revision_idx, revision in enumerate(revisions):
            logger.info(
                self.logger_prefix
                + "Revision {}/{} <{}>".format(
                    revision_idx + 1, revisions_count, revision
                )
            )

            if is_auto_checkout:
                self.checkout(revision, True)
            with io.cd(self.checkout_dir):
                func_revision(self, revision)
