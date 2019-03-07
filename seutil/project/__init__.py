import os
import sys

module_root = os.path.dirname(os.path.realpath(__file__)) + "/../.."
if module_root not in sys.path:
    sys.path.insert(0, module_root)


from .Project import Project
from .ProjectResults import ProjectResults

__all__ = [
    "Project",
    "ProjectResults",
]
