import subprocess

from typing import *


class BashUtils:
    """
    Utility functions for running Bash commands.
    """

    class RunResult(NamedTuple):
        return_code: int
        stdout: str
        stderr: str

    @classmethod
    def run(cls, cmd: str,
            expected_return_code: int = None) -> RunResult:
        """
        Runs a Bash command and returns the stdout.
        :param cmd: the command to run.
        :param expected_return_code: if set to an int, will raise exception if the return code mismatch.
        :return: the run result, which is a named tuple with field return_code, stdout, stderr.
        """
        completed_process = subprocess.run(["bash", "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return_code = completed_process.returncode
        stdout = completed_process.stdout.decode("utf-8", errors="ignore")
        stderr = completed_process.stderr.decode("utf-8", errors="ignore")

        if expected_return_code is not None:
            if return_code != expected_return_code:
                raise RuntimeError(f"Expected {expected_return_code} but returned {return_code} while executing bash command '{cmd}'.\nstdout: {stdout}\nstderr: {stderr}")
        # end if, if

        return cls.RunResult(return_code, stdout, stderr)
