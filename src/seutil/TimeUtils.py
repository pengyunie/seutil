import signal
from contextlib import contextmanager
import time


class TimeoutException(Exception):
    pass


class TimeUtils:
    @classmethod
    @contextmanager
    def time_limit(cls, seconds):
        def signal_handler(signum, frame):
            raise TimeoutException("Timed out after {} seconds!".format(seconds))

        signal.signal(signal.SIGALRM, signal_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)

    def timer(func):
        """
        A decorator that prints how long a function took to run.

        :param func: The function to be decorated.
        """

        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            print(
                "Function: {} args: {} {} took {} seconds to execute.".format(func.__name__, args, kwargs, end - start)
            )
            return result

        return wrapper
