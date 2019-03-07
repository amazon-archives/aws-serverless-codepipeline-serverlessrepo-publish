"""Lambda function handler."""

# must be the first import in files with lambda function handlers
import lambdainit  # noqa: F401

import logging

LOG = logging.getLogger(__name__)


def handler(event, context):
    """Lambda function handler."""
    LOG.info('Received event: %s', event)
