from pathlib import Path
from typing import *

from .. import IOUtils, Stream


class ProjectResults:

    def __init__(self):
        self.full_name: str = "UNKNOWN"
        self.results_dir: Path = None
        return

    @classmethod
    def from_base_results_dir(cls, base_results_dir: Path) -> List["ProjectResults"]:
        full_names = Stream.of_dirs(base_results_dir)
        return [cls.get_project_results(n, base_results_dir/n) for n in full_names]

    @classmethod
    def get_project_results(cls, full_name: str, results_dir: Path) -> "ProjectResults":
        results = cls()
        results.full_name = full_name
        results.results_dir = results_dir
        return results

    @property
    def meta_dir(self) -> Path:
        meta_dir: Path = self.results_dir / "META"
        meta_dir.mkdir(parents=True, exist_ok=True)
        return meta_dir

    def load_meta_result(self, file_name: str, fmt: str = "json") -> Any:
        return IOUtils.load(self.meta_dir / file_name, fmt)

    def dump_meta_result(self, file_name: str, data: Any, fmt: str = "json") -> None:
        IOUtils.dump(self.meta_dir / file_name, data, fmt)
        return

    def get_revision_dir(self, revision: str) -> Path:
        revision_dir = self.results_dir / revision
        revision_dir.mkdir(parents=True, exist_ok=True)
        return revision_dir

    def load_revision_result(self, revision: str, file_name: str, fmt: str = "json") -> Any:
        return IOUtils.load(self.get_revision_dir(revision) / file_name, fmt)

    def dump_revision_result(self, revision: str, file_name: str, data: Any, fmt: str = "json") -> None:
        IOUtils.dump(self.get_revision_dir(revision) / file_name, data, fmt)
        return
