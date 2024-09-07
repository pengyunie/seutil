import lazy_import

from . import arg, bash, io, log, pbar  # noqa: F401
from .BashUtils import BashUtils  # noqa: F401
from .GitHubUtils import GitHubUtils
from .LoggingUtils import LoggingUtils  # noqa: F401
from .TimeUtils import TimeoutException, TimeUtils

project = lazy_import.lazy_module("seutil.project")
latex = lazy_import.lazy_module("seutil.latex")
ds = lazy_import.lazy_module("seutil.ds")

# tricks the IDE to recognize the lazy imports, so that it can provide code completion
# won't be executed
if 1.0 == 1.01:
    from . import ds, latex, project


__all__ = [
    "arg",
    "bash",
    "powershell",
    "io",
    "log",
    "latex",
    "project",
    "ds",
    "GitHubUtils",
    "MiscUtils",
    "Stream",
    "TimeUtils",
    "TimeoutException",
]
