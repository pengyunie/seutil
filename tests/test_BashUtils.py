from typing import *

import os
import unittest

from seutil import BashUtils


class test_BashUtils(unittest.TestCase):

    TEST_ENV_A_KEY = "TEST_BASHUTILS_ENV_A"
    TEST_ENV_A_VALUE = "aaa"

    def test_inherit_env(self):
        os.environ[self.TEST_ENV_A_KEY] = self.TEST_ENV_A_VALUE
        self.assertEqual(self.TEST_ENV_A_VALUE, BashUtils.run(f"echo -n ${self.TEST_ENV_A_KEY}").stdout)
        return

    def test_propagate_env(self):
        del os.environ[self.TEST_ENV_A_KEY]
        self.assertTrue(self.TEST_ENV_A_KEY not in os.environ)
        self.assertEqual(self.TEST_ENV_A_VALUE, BashUtils.run(f"export {self.TEST_ENV_A_KEY}={self.TEST_ENV_A_VALUE}; echo -n ${self.TEST_ENV_A_KEY}", is_update_env=True).stdout)
        self.assertEqual(self.TEST_ENV_A_VALUE, os.environ[self.TEST_ENV_A_KEY])
