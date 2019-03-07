import os
import unittest
from pathlib import Path

from pyutil import IOUtils
from .TestSupport import TestSupport


class test_IOUtils(unittest.TestCase):

    def test_cd(self):
        with TestSupport.get_playground_path():
            oldpath = Path.cwd()
            testpath = Path("./aaa").resolve()
            testpath.mkdir()
            with IOUtils.cd(testpath):
                # Checks if changed directory successfully
                self.assertEqual(testpath, Path.cwd())
            # end with
            # Checks if returned to old directory successfully
            self.assertEqual(oldpath, Path.cwd())
        # end with
        return


if __name__ == '__main__':
    unittest.main()
