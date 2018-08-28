"""Logging helpers for lambda functions.

Allows for log level to be set dynamically.
"""

import logging
import config


# intentionally breaking naming convention to match logger.getLogger()
def getLogger(name):
    """Initialize logger with given name.

    Sets log level based on configured value.
    """
    log_level = config.LOG_LEVEL
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % log_level)

    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)
    return logger
