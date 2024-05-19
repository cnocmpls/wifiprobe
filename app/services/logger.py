import logging
import sys

from app.dependencies import LOG_LEVEL, LOG_LEVEL_MAPPING


def setup_logger(name):
    logger = logging.getLogger(name)
    log_level = LOG_LEVEL_MAPPING.get(LOG_LEVEL, logging.INFO)
    logger.setLevel(log_level)

    # Create handlers for stdout and stderr
    stdout_handler = logging.StreamHandler(sys.stdout)
    stderr_handler = logging.StreamHandler(sys.stderr)

    # Set logging level for each handler
    stdout_handler.setLevel(log_level)  # Adjust as needed
    stderr_handler.setLevel(logging.ERROR)  # Adjust as needed

    # Set formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    stdout_handler.setFormatter(formatter)
    stderr_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)

    return logger
