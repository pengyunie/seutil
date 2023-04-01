import os

import pytest

import seutil as su


def test_run():
    assert su.bash.run("echo 'hello world'").stdout == "hello world\n"


def test_check_returncode():
    with pytest.raises(su.bash.BashError):
        su.bash.run("echo 'hello world' && exit 1", check_returncode=0)

    with pytest.raises(su.bash.BashError):
        su.bash.run("echo 'hello world'", check_returncode=1)


def test_inherit_env():
    os.environ["TEST_SEUTIL_BASH_ENV"] = "1"
    assert su.bash.run("echo $TEST_SEUTIL_BASH_ENV").stdout == "1\n"


def test_update_env():
    os.environ["TEST_SEUTIL_BASH_ENV"] = "1"
    su.bash.run("export TEST_SEUTIL_BASH_ENV=2", update_env=True)
    assert os.environ["TEST_SEUTIL_BASH_ENV"] == "2"

    os.environ["TEST_SEUTIL_BASH_ENV"] = "1"
    su.bash.run(
        "unset TEST_SEUTIL_BASH_ENV",
        update_env=True,
        update_env_clear_existing=True,
    )
    assert "TEST_SEUTIL_BASH_ENV" not in os.environ
