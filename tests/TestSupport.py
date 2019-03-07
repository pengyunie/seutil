import os
import shutil
from pathlib import Path
import random


class TestSupport:
    """
    Macros, utility functions for tests.
    """
    THIS_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
    PROJECT_DIR = THIS_DIR.parent
    SUBJECTS_DIR = PROJECT_DIR / "test-subjects"

    class get_playground_path:
        SUBJECTS_DIR = None

        def __init__(self, path: Path = None):
            if path is None:
                path = self.SUBJECTS_DIR / "playground_{}".format(random.randint(100000, 999999))
            # end if

            self.path = path  # Path
            if self.path.exists():
                shutil.rmtree(self.path)
            # end if
            self.path.mkdir(exist_ok=True)
            self.old_path = Path.cwd()  # Path
            return

        def __enter__(self):
            os.chdir(self.path)
            return

        def __exit__(self, type, value, tb):
            shutil.rmtree(self.path)
            os.chdir(self.old_path)
            return
    # end class
    get_playground_path.SUBJECTS_DIR = SUBJECTS_DIR
