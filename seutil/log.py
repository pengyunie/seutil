"""
This module assists the logging standard library.  The main functionality is:

* maintain two frequently used handlers: a stderr handler and a file handler, both with
  rich and customizable formats.
* `setup` method to attach them to the root logger.
* `get_logger` method to quickly create a logger with customized level.
"""
import logging
import sys
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Union

__all__ = [
    "setup",
    "get_logger",
]


LOGGING_NAMESPACE = "su"

handler_stderr = logging.StreamHandler(sys.stderr)
handler_file = None


def setup(
    log_file: Optional[Union[str, Path]] = None,
    level_stderr: Union[int, str] = logging.INFO,
    level_file: Union[int, str] = logging.DEBUG,
    fmt_stderr: str = "[{asctime}{levelname[0]}]{name}: {message}",
    datefmt_stderr: str = "%H:%M:%S",
    fmt_file: str = "[{asctime}|{relativeCreated:.3f}|{levelname:7}]{name}: {message} [@{filename}:{lineno}|{funcName}|pid {process}|tid {thread}]",
    datefmt_file: str = "%Y-%m-%d %H:%M:%S",
    clear_handlers: bool = True,
    **kwargs_file: dict,
):
    """
    Setup the stderr and file handlers, and attach them to the root logger.

    :param log_file: the log file to use; if None, no file handler is created (and any existing one would be removed)
    :param level_stderr: the level filter of the stderr handler
    :param level_file: the level filter of the file handler
    :param fmt_stderr: the format of the stderr handler (with {} style)
    :param fmt_file: the format of the file handler (with {} style)
    :param clear_handlers: if True, remove all existing handlers of the root logger; otherwise, keep them as is
    :param kwargs_file: other optional kwargs to the file handler (RotatingFileHandler)
    """
    global handler_stderr, handler_file

    root_logger = logging.getLogger(LOGGING_NAMESPACE)
    root_logger.propagate = False
    # set to NOTSET+1, so that child logger's effective level can be correctly computed based on this logger
    root_logger.setLevel(logging.NOTSET + 1)

    if clear_handlers:
        root_logger.handlers = []

    # update the stderr handler
    handler_stderr.setLevel(level_stderr)
    handler_stderr.setFormatter(
        logging.Formatter(fmt_stderr, datefmt_stderr, style="{")
    )
    root_logger.addHandler(handler_stderr)

    # update the file handler
    root_logger.removeHandler(handler_file)

    if log_file is not None:
        kwargs_file.setdefault("maxBytes", 10_000_000)
        kwargs_file.setdefault("backupCount", 1)
        handler_file = RotatingFileHandler(log_file, **kwargs_file)
        handler_file.setLevel(level_file)
        handler_file.setFormatter(logging.Formatter(fmt_file, datefmt_file, style="{"))

        root_logger.addHandler(handler_file)
    else:
        handler_file = None


def get_logger(name: str, level: Union[int, str] = logging.NOTSET):
    """
    Get a logger with specified name and level.
    """
    logger = logging.getLogger(LOGGING_NAMESPACE + "." + name)
    logger.setLevel(level)
    return logger
