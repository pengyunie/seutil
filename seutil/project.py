import dataclasses
import sys
import traceback
from pathlib import Path
from types import TracebackType
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from tqdm import tqdm

from . import bash, io, log

logger = log.get_logger(__name__, log.INFO)


ExcInfo = Tuple[BaseException, BaseException, TracebackType]


class CollatedErrors(Exception):
    def __init__(self, contexts: List[str], exc_infos: List[ExcInfo]):
        assert len(contexts) == len(exc_infos)
        self.contexts = contexts
        self.exc_infos = exc_infos

    def __str__(self):
        s = f"Total {len(self.exc_infos)} errors:"
        for i, (c, e) in enumerate(zip(self.contexts, self.exc_infos)):
            s += f"\n #{i}: {c}\n{traceback.format_exception(*e)}"
        return s

    def __repr__(self):
        return f"{self.__class__.__name__} with {len(self.exc_infos)} errors"


@dataclasses.dataclass
class Project:
    """
    Data structure to represent a software project using a version control system (currently only git is supported).

    A collection of `Project` can be saved to a json/yaml file, as a corpus of software projects.
    `Project` provides common version control operations, such as cloning, checking out, etc.

    :param full_name: the full name of the project; this name is used as the directory/file name when operating on the project, so it should be unique and path-safe (i.e., does not contain '/', ' ', or other special characters that could cause trouble being a path). The recommended name for a project $repo/$name is $repo_$name (it is unique if $repo does not contain '_', which is the case at least for GitHub).
    :param clone_url: the URL to clone the project from.
    :param data: other information of the project stored in key-value pairs, such as revision, branch, etc.; keys should be string and values should be serializable.
    """

    full_name: str
    clone_url: str
    data: Dict[str, Any] = dataclasses.field(default_factory=dict)

    _dir: dataclasses.InitVar[Path] = None

    @property
    def dir(self) -> Path:
        self.require_cloned()
        return self._dir

    @classmethod
    def from_github_url(
        cls,
        url: str,
        revision: Optional[str] = None,
        default_branch: Optional[str] = None,
    ) -> "Project":
        """
        TODO: Creates a Project from a GitHub URL.
        """
        raise NotImplementedError()

    def clone(
        self, downloads_dir: Path, name: Optional[str] = None, exists: str = "ignore"
    ) -> None:
        """
        Clones the project to a local directory, such that more operations can be performed on it.
        :param downloads_dir: the parent directory to clone the project to.
        :param name: the name of the sub-directory to clone the project to; if not provided, `full_name` will be used.
        :param exists: the action to take if the directory already exists:
            * ignore (default): do nothing.
            * remove: remove the directory and clone the project again.
            * pull: update the project by pulling the latest changes; may fail if there is no internet connection or the remote url is not accessible any more.
            * error: raise an error.
        """
        if name is None:
            name = self.full_name
        assert exists in ["ignore", "remove", "pull", "error"]
        logger.info(f"Project {self.full_name}: cloning to {downloads_dir / name}")

        if (downloads_dir / name).exists():
            if exists == "ignore":
                self._dir = downloads_dir / name
                logger.info(
                    f"Project {self.full_name}: existing at {downloads_dir / name}"
                )
                return
            elif exists == "remove":
                io.rmdir(downloads_dir / name)
                logger.info(
                    f"Project {self.full_name}: removed existing at {downloads_dir / name}"
                )
            elif exists == "pull":
                self._dir = downloads_dir / name
                logger.info(
                    f"Project {self.full_name}: existing at {downloads_dir / name}"
                )
                self.fetch()
                return
            elif exists == "error":
                raise RuntimeError(
                    f"Project {self.full_name}: can not clone to existing directory {downloads_dir}/{name}"
                )

        io.mkdir(downloads_dir)
        with io.cd(downloads_dir):
            bash.run(f"git clone {self.clone_url} {name}", 0)
        self._dir = downloads_dir / name

    def set_cloned_dir(self, dir: Path) -> None:
        """
        Tells the project that it has been cloned to the given directory, such that more operations can be performed on it.
        We will trust that you provided a valid directory.
        """
        self._dir = dir
        logger.info(f"Project {self.full_name}: set to be cloned at {dir}")

    def remove(self, error_not_exists: bool = False) -> None:
        """
        Removes the project from the local directory.
        :param error_not_exists: if True, raise an error if the project has not been cloned yet.
        """
        if self._dir is None:
            if error_not_exists:
                raise RuntimeError(
                    f"Project {self.full_name}: not cloned yet, can not remove"
                )
            else:
                logger.info(f"Project {self.full_name}: already removed")
        else:
            io.rmdir(self._dir)
            self._dir = None
            logger.info(f"Project {self.full_name}: removed")

    def require_cloned(self, operation: Optional[str] = None) -> None:
        error_msg = f"Project {self.full_name}: needs to be cloned"
        if operation is not None:
            error_msg += f" before performing the {operation} operation"
        if self._dir is None:
            raise RuntimeError(error_msg)

    def fetch(self) -> None:
        """
        Updates the project by pulling the latest changes.
        May fail if there is no internet connection or the remote url is not accessible any more.
        """
        self.require_cloned("fetch")
        logger.info(f"Project {self.full_name}: fetching latest changes")
        with io.cd(self._dir):
            bash.run("git fetch --all", 0)

    def checkout(self, revision: str, forced: bool = False) -> None:
        """
        Checks out the given revision (or branch or tag) of the project.
        :param revision: the revision (or branch or tag) to checkout.
        :param forced: if True, do force checkout (discarding all local changes that might prevent a checkout).
        """
        self.require_cloned("checkout")
        logger.info(
            f"Project {self.full_name}: checking out revision {revision} ({forced=})"
        )

        with io.cd(self._dir):
            cmd = f"git checkout {revision}"
            if forced:
                cmd += " -f"
            bash.run(cmd, 0)

    def get_cur_revision(self) -> str:
        """
        Gets the current revision of the project.
        """
        self.require_cloned("get_cur_revision")
        with io.cd(self._dir):
            revision = bash.run("git log --pretty='%H' -1", 0).stdout.strip()
        return revision

    def get_revisions_lattice(self):
        """
        TODO: Gets the revisions lattice of the project, ending at the current revision.
        """
        raise NotImplementedError()

    def for_each_revision(
        self,
        func: Callable[["Project", str], Any],
        revisions: Iterable[str],
        is_auto_checkout: bool = True,
        errors: str = "collate",
        pbar: Optional[tqdm] = None,
    ) -> List[Any]:
        """
        Runs the func_revision for each revision.

        :param func: the function to run, which takes a Project object and a string revision.
        :param revisions: the revisions to run the function on.
        :param is_auto_checkout: if set to False, will not automatically checkout each revision (for example, if func does that itself, or if func does not need the project to be checked out at the given revision).
        :param errors: what to do if the function throws errors:
            * ignore: do nothing, not even say a word.
            * warning: make a log.warning for each error.
            * collate (default): collect all errors, and raise a CollatedErrors at the end.
            * error: raise immediately after the first error.
        :param pbar: if provided, the (tqdm) progress bar to use; only the description and the count of the progress bar will be updated, but the total should be set before entering this function.
        :return: the list of return values of the function.
        """
        assert errors in ["ignore", "warning", "collate", "error"]
        self.require_cloned("for_each_revision")

        results = []
        errored_revisions = []
        exc_infos = []

        for revision in revisions:
            if pbar is not None:
                pbar.set_description(f"Revision {revision}")

            try:
                if is_auto_checkout:
                    self.checkout(revision, True)
                with io.cd(self.checkout_dir):
                    results.append(func(self, revision))
            except KeyboardInterrupt:
                raise
            except:
                if errors == "ignore":
                    pass
                elif errors == "warning":
                    logger.warning(
                        f"Project {self.full_name}: error at revision {revision}: {traceback.format_exc()}"
                    )
                elif errors == "collate":
                    logger.warning(
                        f"Project {self.full_name}: error at revision {revision}: {traceback.format_exc()}"
                    )
                    errored_revisions.append(revision)
                    exc_infos.append(sys.exc_info())
                elif errors == "error":
                    raise
            finally:
                if pbar is not None:
                    pbar.update(1)

        if errors == "collate" and len(exc_infos) > 0:
            raise CollatedErrors(errored_revisions, exc_infos)
        return results