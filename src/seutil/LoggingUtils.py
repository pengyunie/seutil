import logging
import sys
from logging.handlers import RotatingFileHandler


class LoggingUtils:

    logging_format = "[{relativeCreated:6.0f}{levelname[0]}]{name}: {message}"
    logging_format_detail = "[{asctime}|{relativeCreated:.3f}|{levelname:7}]{name}: {message} [@{filename}:{lineno}|{funcName}|pid {process}|tid {thread}]"

    # Copied from logging
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    @classmethod
    def get_handler_console(cls, stream=sys.stderr, level=logging.WARNING) -> logging.Handler:
        handler = logging.StreamHandler(stream=stream)
        handler.setLevel(level=level)
        handler.setFormatter(logging.Formatter(cls.logging_format, style="{"))
        return handler

    @classmethod
    def get_handler_file(cls, filename, level=logging.DEBUG) -> logging.Handler:
        handler = RotatingFileHandler(filename, maxBytes=10_000_000, backupCount=1)
        handler.setLevel(level=level)
        handler.setFormatter(logging.Formatter(cls.logging_format_detail, style="{"))
        return handler

    default_level = logging.WARNING
    default_handlers = list()

    @classmethod
    def setup(cls, level=logging.WARNING, filename: str = None):
        logging.basicConfig(level=level, format=cls.logging_format, style="{")

        cls.default_level = level
        cls.default_handlers.clear()
        cls.default_handlers.append(cls.get_handler_console(level=level))
        if filename is not None:
            cls.default_level = logging.DEBUG
            cls.default_handlers.append(cls.get_handler_file(filename=filename))
        # end if
        cls.refresh_loggers()
        return

    loggers = list()

    @classmethod
    def get_logger(cls, name: str,
                   level: int = None) -> logging.Logger:
        if level is None:
            level = cls.default_level
        # end if

        # Always use the same handlers
        handlers = cls.default_handlers

        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.handlers = []
        logger.propagate = False
        for handler in handlers:
            logger.addHandler(handler)
        # end for
        cls.loggers.append(logger)
        return logger

    @classmethod
    def refresh_loggers(cls):
        """
        Refresh all the loggers to use the default handlers.
        """
        handlers = cls.default_handlers
        for logger in cls.loggers:
            logger.handlers = []
            for handler in handlers:
                logger.addHandler(handler)
            # end for
        # end for
        return

    @classmethod
    def log_and_raise(cls, logger: logging.Logger, msg: str, error_type, level: int = ERROR):
        logger.log(level, msg)
        raise error_type(msg)
