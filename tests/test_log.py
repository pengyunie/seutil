import logging

import seutil as su
from seutil.log import LOGGING_NAMESPACE


def test_log():
    # only setup stderr handler
    su.log.setup()
    logger = su.log.get_logger(__name__)
    logger.info(f"[0] Test logging to stderr only")
    assert len(logging.getLogger(LOGGING_NAMESPACE).handlers) == 1

    # setup both stderr handler and file handler
    f1 = su.io.mktmp("seutil", ".txt")
    su.log.setup(f1)
    assert len(logging.getLogger(LOGGING_NAMESPACE).handlers) == 2
    logger.info(f"[1] Test logging to f1 {f1}")
    logf1_1 = su.io.load(f1)
    assert len(logf1_1) > 0

    # setup a different file handler
    f2 = su.io.mktmp("seutil", ".txt")
    su.log.setup(f2)
    assert len(logging.getLogger(LOGGING_NAMESPACE).handlers) == 2
    logger.info(f"[2] Test logging to f2 {f2}")
    logf1_2 = su.io.load(f1)
    logf2_2 = su.io.load(f2)
    assert len(logf2_2) > 0
    assert logf1_1 == logf1_2

    # again, only setup stderr handler
    su.log.setup()
    assert len(logging.getLogger(LOGGING_NAMESPACE).handlers) == 1
    logger.info(f"[3] Test logging to stderr only")
    logf1_3 = su.io.load(f1)
    logf2_3 = su.io.load(f2)
    assert logf1_2 == logf1_3
    assert logf2_2 == logf2_3

    # clean up
    su.io.rm(f1)
    su.io.rm(f2)


# TODO: this test current fails after test_log, probably fix it by adding an adhoc caplog fixture
def test_caplog_still_work(caplog):
    caplog.clear()
    logger = su.log.get_logger(__name__, level=logging.INFO)
    logger.info("hello world")
    assert len(caplog.records) == 1
