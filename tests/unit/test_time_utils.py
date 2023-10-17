import seutil as su
from seutil.TimeUtils import timer
import pytest


def test_timer():
    @timer
    def foo(n: int):
        for i in range(n):
            for j in range(n):
                i * j

    foo(100000)
