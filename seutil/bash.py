import os
import subprocess
import warnings
from typing import Optional

from seutil import io


class BashError(RuntimeError):
    def __init__(
        self,
        cmd: str,
        completed_process: subprocess.CompletedProcess,
        check_returncode: int,
    ):
        self.cmd = cmd
        self.returncode = completed_process.returncode
        self.check_returncode = check_returncode
        self.stdout = completed_process.stdout
        self.stderr = completed_process.stderr

    def __str__(self) -> str:
        s = f"Command '{self.cmd}' failed with returncode {self.returncode}, expected returncode {self.check_returncode}.\n"
        show_full_output = os.environ.get("SEUTIL_SHOW_FULL_OUTPUT", "0") == "1"
        if show_full_output:
            s += f"STDOUT:\n{self.stdout}\n"
            s += f"STDERR:\n{self.stderr}\n"
        else:
            if len(self.stdout) > 200:
                s += f"STDOUT (truncated, set SEUTIL_SHOW_FULL_OUTPUT=1 to see full output):\n{self.stdout[:100]}...{self.stdout[-100:]}\n"
            else:
                s += f"STDOUT:\n{self.stdout}\n"
            if len(self.stderr) > 200:
                s += f"STDERR (truncated, set SEUTIL_SHOW_FULL_OUTPUT=1 to see full output):\n{self.stderr[:100]}...{self.stderr[-100:]}\n"
            else:
                s += f"STDERR:\n{self.stderr}\n"
        return s

    def __repr__(self) -> str:
        return self.__str__()


def run(
    cmd: str,
    check_returncode: Optional[int] = None,
    warn_nonzero: bool = True,
    update_env: bool = False,
    update_env_clear_existing: bool = False,
    **kwargs,
) -> subprocess.CompletedProcess:
    """
    Run a bash command using subprocess.run.  The command will be run using "bash -c".

    Some arguments' default values are changed (but can be overridden with kwargs):
    * capture_output=True, text=True:  capture all stdout and stderr.

    This function is able to check if return code match a given value (subprocess only supports
    checking non-zero values, but this function supports any).  Nevertheless, this function
    warns about any non-zero values if check_returncode is not set, to avoid silent failures;
    this behavior can be turned off via warn_nonzero=False.

    In addition, this function can try to update the environment variables in this process
    with the ones after running the command (if the command finished successfully).
    The retrival of the sub shell's environments is done by `env` into a temporary file.

    :param cmd: the command to run
    :param check_returncode: the return code to expect from the command
    :param warn_nonzero: whether to warn about non-zero exit codes
    :param update_env: whether to update the environment variables in this process
    :param update_env_clear_existing: whether to clear existing environment variables before updating
    :param kwargs: other arguments passed to subprocess.run
    :return: the subprocess.CompletedProcess object, has stdout, stderr, returncode fields
    :raises: BashError if the command's output did not match check_returncode
    :raises: subprocess.TimeoutExpired if the command timed out
    """
    # If update env is requested, append `env` to command
    if update_env:
        tempfile_update_env = io.mktmp("seutil-bash", ".txt")
        cmd += f" ; env > {tempfile_update_env}"

    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)

    completed_process = subprocess.run(
        ["bash", "-c", cmd],
        **kwargs,
    )

    # check return code
    if (
        check_returncode is not None
        and completed_process.returncode != check_returncode
    ):
        raise BashError(cmd, completed_process, check_returncode)

    if (
        completed_process.returncode != 0
        and check_returncode is not None
        and warn_nonzero
    ):
        warnings.warn(
            f"Bash command `{cmd}` returned non-zero exit code: {completed_process.returncode}",
            RuntimeWarning,
        )

    if update_env:
        envs = io.load(tempfile_update_env, io.Fmt.txtList)
        if update_env_clear_existing:
            os.environ.clear()
        for env in envs:
            key, value = env.split("=", 1)
            os.environ[key] = value
        io.rm(tempfile_update_env)

    return completed_process
