import re
import time

import pytest

import seutil as su


def test_time_func_stdout(capsys: pytest.CaptureFixture):
    @su.time.time_func
    def foo(n: int):
        for i in range(n):
            for j in range(n):
                i * j

    foo(1000)
    captured = capsys.readouterr()
    assert re.fullmatch(r"Function: foo args: \(1000,\) {} took \d+\.\d+ seconds to execute.\n", captured.out)


def test_time_func_record():
    times = []

    @su.time.time_func(record_callback=times.append)
    def foo():
        time.sleep(0.01)

    for _ in range(10):
        foo()
    assert len(times) == 10
    assert all(t >= 0.01 for t in times)
