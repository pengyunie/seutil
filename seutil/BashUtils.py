import subprocess

from typing import *


class BashUtils:
    """
    Utility functions for running Bash commands.
    """

    @classmethod
    def run(cls, cmd: str,
            expected_return_code: int = None,
            is_get_return_code: bool = False,
            is_get_stdout: bool = True,
            is_get_stderr: bool = False) -> Any:
        """
        Runs a Bash command and returns the stdout.
        :param cmd: the command to run.
        :param expected_return_code: if set to an int, will raise exception if the return code mismatch.
        :param is_get_return_code: if get the return code.
        :param is_get_stdout: if get the stdout content.
        :param is_get_stderr: if get the stderr content.
        If multiple return values are requested, the values are returned in a tuple with the order (return_code, stdout, stderr).
        :return: stdout.
        """
        completed_process = subprocess.run(["bash", "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if expected_return_code is not None:
            if completed_process.returncode != expected_return_code:
                raise RuntimeError(f"Expected {expected_return_code} but returned {completed_process.returncode}; While executing bash command '{cmd}'.")
        # end if, if

        return_values = []
        if is_get_return_code:
            return_values.append(completed_process.returncode)
        if is_get_stdout:
            return_values.append(completed_process.stdout.decode("utf-8", errors="ignore"))
        if is_get_stderr:
            return_values.append(completed_process.stderr.decode("utf-8", errors="ignore"))

        if len(return_values) == 0:
            return None
        elif len(return_values) == 1:
            return return_values[0]
        else:
            return return_values
