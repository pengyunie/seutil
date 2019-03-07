import os
import unittest
import logging
from pyutil.LoggingUtils import LoggingUtils


class test_LoggingUtils(unittest.TestCase):

    def test_logging(self):
        LoggingUtils.setup(logging.INFO)
        logger = LoggingUtils.get_logger(self.test_logging.__name__)
        logger.warning("A sample warning message.")
        logger.info("A sample info message")
        return

    def test_logging_file(self):
        file_name = "/tmp/aaa.txt"
        if os.path.isfile(file_name):
            os.remove(file_name)
        # end if

        LoggingUtils.setup(logging.WARNING, file_name)
        logger = LoggingUtils.get_logger(self.test_logging_file.__name__)
        logger.debug("Debug")
        logger.info("Info")
        logger.error("Error")

        with open(file_name, "r") as f:
            print(f.read())
        # end with
        return
