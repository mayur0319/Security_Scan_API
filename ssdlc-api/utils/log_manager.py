import os
import logging
from utils.config import CURRENT_ENVIRONMENT

class LogManager:
    """
    A singleton logger class to manage application-wide logging.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LogManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

        if CURRENT_ENVIRONMENT == "prod":
            level = logging.INFO
        else:
            level = logging.DEBUG

        self.logger.setLevel(level)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s %(name)s [%(levelname)s]: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def info(self, message: str):
        """Log info level messages."""
        self.logger.info(message)

    def debug(self, message: str):
        """Log debug level messages."""
        self.logger.debug(message)

    def warning(self, message: str):
        """Log warning level messages."""
        self.logger.warning(message)

    def error(self, message: str):
        """Log error messages with stack trace."""
        self.logger.error(message, exc_info=True)

    def exception(self, message: str):
        """Log exception messages with stack trace."""
        self.logger.exception(message, exc_info=True)
