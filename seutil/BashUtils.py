from typing import *

import os
from pathlib import Path
import subprocess


class BashUtils:
    """
    Utility functions for running Bash commands.
    """
    PRINT_LIMIT = 1000

    class RunResult(NamedTuple):
        return_code: int
        stdout: str
        stderr: str

    @classmethod
    def run(cls, cmd: str,
            expected_return_code: int = None,
            is_update_env: bool = False,
    ) -> RunResult:
        """
        Runs a Bash command and returns the stdout.
        :param cmd: the command to run.
        :param expected_return_code: if set to an int, will raise exception if the return code mismatch.
        :param is_update_env: if true, the environment in *this python process (os.environ)* will be updated upon the successful execution of cmd (i.e., returns 0), to reflect the changes to the enrionment variables cmd may make.  Note it can not change the environment of the process that invoked this python process.  It is useful because the updated environment will be used for later BashUtils.run executions.
        :return: the run result, which is a named tuple with field return_code, stdout, stderr.
        """
        # If update env is requested, append an additional command to the cmd
        if is_update_env:
            tempfile_update_env = cls.get_temp_file()
            cmd += f" && env > {tempfile_update_env}"
        # end if

        completed_process = subprocess.run(["bash", "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #completed_process = subprocess.run(cmd, shell=True, executable="/bin/bash", stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return_code = completed_process.returncode
        stdout = completed_process.stdout.decode("utf-8", errors="ignore")
        stderr = completed_process.stderr.decode("utf-8", errors="ignore")

        # Update env, if requested and return code is 0
        if is_update_env and return_code == 0:
            with open(str(tempfile_update_env), "r") as fp:
                os.environ.clear()
                for line in fp.read().splitlines(keepends=False):
                    env_key, env_value = line.split(sep="=", maxsplit=1)
                    os.environ[env_key] = env_value
                # end for
            # end with
        # end if

        if expected_return_code is not None:
            if return_code != expected_return_code:
                if len(stdout) > cls.PRINT_LIMIT:
                    tempfile_stdout = subprocess.run(["bash", "-c", "mktemp"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode("utf-8", errors="ignore").strip()
                    with open(tempfile_stdout, "w") as f:
                        f.write(stdout)
                    # end with
                    stdout = f"{stdout[:cls.PRINT_LIMIT]} //////////TOO LONG; dumped to {tempfile_stdout}//////////"
                # end if
                if len(stderr) > cls.PRINT_LIMIT:
                    tempfile_stderr = subprocess.run(["bash", "-c", "mktemp"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode("utf-8", errors="ignore").strip()
                    with open(tempfile_stderr, "w") as f:
                        f.write(stderr)
                    # end with
                    stderr = f"{stderr[:cls.PRINT_LIMIT]} //////////TOO LONG; dumped to {tempfile_stderr}//////////"
                # end if
                raise RuntimeError(f"Expected {expected_return_code} but returned {return_code} while executing bash command '{cmd}'.\nstdout: {stdout}\nstderr: {stderr}")
        # end if, if

        return cls.RunResult(return_code, stdout, stderr)

    @classmethod
    def get_temp_dir(cls) -> Path:
        return Path(cls.run("mktemp -d", expected_return_code=0).stdout.strip())

    @classmethod
    def get_temp_file(cls) -> Path:
        return Path(cls.run("mktemp", expected_return_code=0).stdout.strip())
