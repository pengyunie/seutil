import functools
import signal
import sys
import time
from contextlib import contextmanager
from typing import Callable, Optional, TextIO


class TimeoutException(Exception):
    pass


@contextmanager
def time_limit(seconds: int):
    """
    Requires the containing code block to finish within the time limit given in seconds.
    If the code block does not finish in time, its execution will be interrupted (by
    SIGALRM) and a TimeoutException is raised.

    However, if the code block spawns a external process (e.g., running a Bash command),
    its execution may not be interrupted before that external process finishes (but a
    TimeoutException will still be raised at the end of execution). The exact scenario
    that will trigger this problem and the root cause is not clear yet.

    :param seconds: The time limit in seconds.
    :raises TimeoutException: If the code block does not finish within the time limit.
    """

    def signal_handler(signum, frame):
        raise TimeoutException(f"Timed out after {seconds} seconds!")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


def time_func(
    _func=None,
    *,
    print_to: Optional[TextIO] = None,
    record_callback: Optional[Callable[[float], None]] = None,
    fmt: str = ".3f",
):
    """
    Decorates a function to print/record its execution time when it executes.

    If the function raises an exception, the execution time will still be
    printed/recorded before the exception is propagated.

    Usage:
    ```
    # print to stdout
    @su.time.timer
    def foo(): ...

    # save the execution time to some global variable, e.g., a list
    list_times = []
    @su.time.timer(record_callback=list_times.append)
    def bar(): ...
    ```

    :param func: The function to be decorated.
    :param print_to: The place to print the execution time. If neither print_to nor
        record_callback is given, print to stdout.
    :param record_callback: A callback function to record the execution time, should
        take exactly one float parameter.
    """

    def decorator_timer(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal print_to, record_callback, fmt
            start = time.time()
            try:
                result = func(*args, **kwargs)
            finally:
                end = time.time()

                time_taken = end - start
                if print_to is None and record_callback is None:
                    print_to = sys.stdout
                if print_to is not None:
                    print(
                        f"Function: {func.__name__} args: {args} {kwargs} took {time_taken:{fmt}} seconds to execute.",
                        file=print_to,
                    )
                if record_callback is not None:
                    record_callback(time_taken)
                return result

        return wrapper

    if _func is None:
        return decorator_timer
    else:
        return decorator_timer(_func)


class Timer:
    """
    Records the start/end/elapsed time to execute a code block.

    Usage:
    ```
    with su.time.Timer() as timer:
        ...
    print(f"Execution took {timer.elapsed}s"
    print(f"... started at {timer.start}, ended at {timer.end}")
    ```
    """

    def __init__(self):
        self.start: float = None
        self.end: float = None
        self.elapsed: float = None

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.time()
        self.elapsed = self.end - self.start
