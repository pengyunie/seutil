import signal
from contextlib import contextmanager


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
