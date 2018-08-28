"""Lambda function entrypoint handlers."""

import lambdainit  # noqa: F401
import log_helper

LOGGER = log_helper.getLogger(__name__)


def publish(request, context):
    """Publish to Serverless Apps Repo.

    CodePipeline invokes the lambda to publish an application
    to Serverless Apps repo.
    """
    LOGGER.info('CodePipeline publish to repo request=%s', request)

    return {}
