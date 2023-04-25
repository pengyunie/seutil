import os
import sys

module_root = os.path.dirname(os.path.realpath(__file__)) + "/.."
if module_root not in sys.path:
    sys.path.insert(0, module_root)

import lazy_import

from . import arg, bash, io, log, pbar
from .BashUtils import BashUtils
from .GitHubUtils import GitHubUtils
from .IOUtils import IOUtils
from .LoggingUtils import LoggingUtils
from .Stream import Stream
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

# Remove temporary names
del os
del sys
del module_root
