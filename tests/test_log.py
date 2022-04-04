import logging
import unittest

import seutil as su
from seutil.log import LOGGING_NAMESPACE


class test_log(unittest.TestCase):
    def test_setup(self):
        # only setup stderr handler
        su.log.setup()
        logger = su.log.get_logger(__name__)
        logger.info(f"[0] Test logging to stderr only")
        self.assertEqual(1, len(logging.getLogger(LOGGING_NAMESPACE).handlers))

        # setup both stderr handler and file handler
        f1 = su.io.mktmp("seutil", ".txt")
        su.log.setup(f1)
        self.assertEqual(2, len(logging.getLogger(LOGGING_NAMESPACE).handlers))
        logger.info(f"[1] Test logging to f1 {f1}")
        logf1_1 = su.io.load(f1)
        self.assertTrue(len(logf1_1) > 0)

        # setup a different file handler
        f2 = su.io.mktmp("seutil", ".txt")
        su.log.setup(f2)
        self.assertEqual(2, len(logging.getLogger(LOGGING_NAMESPACE).handlers))
        logger.info(f"[2] Test logging to f2 {f2}")
        logf1_2 = su.io.load(f1)
        logf2_2 = su.io.load(f2)
        self.assertTrue(len(logf2_2) > 0)
        self.assertEqual(logf1_1, logf1_2)

        # again, only setup stderr handler
        su.log.setup()
        self.assertEqual(1, len(logging.getLogger(LOGGING_NAMESPACE).handlers))
        logger.info(f"[3] Test logging to stderr only")
        logf1_3 = su.io.load(f1)
        logf2_3 = su.io.load(f2)
        self.assertEqual(logf1_2, logf1_3)
        self.assertEqual(logf2_2, logf2_3)

        # clean up
        su.io.rm(f1)
        su.io.rm(f2)
