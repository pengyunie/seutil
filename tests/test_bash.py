import os
import unittest

import seutil as su


class test_bash_run(unittest.TestCase):
    def test_run(self):
        self.assertEqual("hello world\n", su.bash.run("echo 'hello world'").stdout)

    def test_run_fail(self):
        self.assertRaises(
            su.bash.BashError,
            su.bash.run,
            "echo 'hello world' && exit 1",
            check_returncode=0,
        )
        self.assertRaises(
            su.bash.BashError, su.bash.run, "echo 'hello world'", check_returncode=1
        )

    def test_inherit_env(self):
        os.environ["TEST_SEUTIL_BASH_ENV"] = "1"
        self.assertEqual("1\n", su.bash.run("echo $TEST_SEUTIL_BASH_ENV").stdout)

    def test_update_env(self):
        os.environ["TEST_SEUTIL_BASH_ENV"] = "1"
        su.bash.run("export TEST_SEUTIL_BASH_ENV=2", update_env=True)
        self.assertEqual("2", os.environ["TEST_SEUTIL_BASH_ENV"])

        os.environ["TEST_SEUTIL_BASH_ENV"] = "1"
        su.bash.run(
            "unset TEST_SEUTIL_BASH_ENV",
            update_env=True,
            update_env_clear_existing=True,
        )
        self.assertTrue("TEST_SEUTIL_BASH_ENV" not in os.environ)
