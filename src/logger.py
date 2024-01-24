import logging



def configure_logging(log_level):
    # Set the logging level based on the user input
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )


    logger = logging.getLogger(__name__)

    logger.info(f'Logging level set to {log_level}')
