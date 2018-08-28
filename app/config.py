"""Configuration values used by lambda functions."""

import os

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
