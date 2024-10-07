import logging
import logging.config

CONSOLE_LOGGER_HANDLER_INDEX = 0

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console_format": {"format": "%(message)s"},
    },
    "handlers": {
        "console": {"level": "INFO", "class": "logging.StreamHandler", "formatter": "console_format"},
    },
    "loggers": {
        "": {"handlers": ["console"], "level": "DEBUG", "propagate": True},  # Root logger
    },
}


def configure_logging():
    """
    Configure the logging settings.

    Returns:
        None
    """
    # Configure the logging settings using the LOGGING_CONFIG dictionary
    logging.config.dictConfig(LOGGING_CONFIG)


def set_console_to_verbose():
    """
    Set the console output to verbose (DEBUG).

    Returns:
        None
    """
    # Get the root logger
    root_logger = logging.getLogger()
    # Get the console handler
    console_handler = root_logger.handlers[CONSOLE_LOGGER_HANDLER_INDEX]
    # Set the console handler to the new log level
    console_handler.setLevel("DEBUG")
