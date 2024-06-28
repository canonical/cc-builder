import logging
import logging.config

CONSOLE_LOGGER_HANDLER_INDEX = 0
FILE_LOGGER_HANDLER_INDEX = 1

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'file_format': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'console_format': {
            'format': '%(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'console_format'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'file_format',
            'filename': 'not-cloud-init.log',  # Log file location
            'mode': 'a',
        },
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True
        },
    }
}

def configure_logging(log_level: str = "DEBUG"):
    """
    Configure the logging settings.

    Args:
        log_level (str): The desired log level. Defaults to "DEBUG".

    Raises:
        ValueError: If an invalid log level is provided.

    Returns:
        None
    """
    # Set the logging level based on the user input
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    logging.config.dictConfig(LOGGING_CONFIG)
        
    # Set log level for file handler
    root_logger = logging.getLogger()
    file_handler = root_logger.handlers[FILE_LOGGER_HANDLER_INDEX]
    file_handler.setLevel(numeric_level)

    logger = logging.getLogger(__name__)

    logger.debug(f"Logging level set to {log_level}")

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