import os
import time
from pathlib import Path

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


def test_issue67_pass(tmp_path: Path):
    temp_script = tmp_path / "z.sh"
    su.io.dump(
        temp_script,
        """#!/bin/bash
echo > z.txt
sleep 0.2
echo "done" >> z.txt""",
        fmt=su.io.fmts.txt,
    )
    temp_script.chmod(0o755)
    with su.io.cd(tmp_path):
        with pytest.raises(su.bash.TimeoutExpired):
            su.bash.run("./z.sh", timeout=0.1)
        time.sleep(0.2)
        assert "done" not in su.io.load("z.txt")


def test_issue67_fail1(tmp_path: Path):
    temp_script = tmp_path / "z.sh"
    su.io.dump(
        temp_script,
        """#!/bin/bash
echo > z.txt
sleep 0.2
echo "done" >> z.txt""",
        fmt=su.io.fmts.txt,
    )
    temp_script.chmod(0o755)
    with su.io.cd(tmp_path):
        with pytest.raises(su.bash.TimeoutExpired):
            su.bash.run("./z.sh > a.txt", timeout=0.1)
        time.sleep(0.2)
        assert "done" not in su.io.load("z.txt")


def test_issue67_fail2(tmp_path: Path):
    temp_script = tmp_path / "z.sh"
    su.io.dump(
        temp_script,
        """#!/bin/bash
echo > z.txt
sleep 0.2
echo "done" >> z.txt""",
        fmt=su.io.fmts.txt,
    )
    temp_script.chmod(0o755)
    with su.io.cd(tmp_path):
        with pytest.raises(su.bash.TimeoutExpired):
            su.bash.run("./z.sh 2>&1", timeout=0.1)
        time.sleep(0.2)
        assert "done" not in su.io.load("z.txt")
