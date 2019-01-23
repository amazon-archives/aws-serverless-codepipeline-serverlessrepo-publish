"""Lambda function handler."""

# must be the first import in files with lambda function handlers
import lambdainit  # noqa: F401
import lambdalogging
import s3helper
import codepipelinehelper

import serverlessrepo
import copy

LOG = lambdalogging.getLogger(__name__)

HIDDEN_VALUE = '__HIDDEN__'


def publish(event, context):
    """Publish to AWS Serverless Application Repository.

    CodePipeline invokes the lambda to publish an application
    to AWS Serverless Application Repository. If the application
    already exists, it will update the application metadata. Besides,
    it will create an application version if SemanticVersion is specified
    in the Metadata section of the packaged template.

    Arguments:
        event {dict} -- The JSON event sent to AWS Lambda by AWS CodePipeline
        (https://docs.aws.amazon.com/codepipeline/latest/userguide/actions-invoke-lambda-function.html#actions-invoke-lambda-function-json-event-example)
        context {LambdaContext} -- The context passed by AWS Lambda
    """
    job_id = event['CodePipeline.job']['id']

    redacted_event = _remove_sensitive_items_from_event(event)
    LOG.info('CodePipeline publish to SAR request={}'.format(redacted_event))

    try:
        packaged_template_str = s3helper.get_input_artifact(event)
        LOG.info('Making API calls to AWS Serverless Application Repository...')
        sar_response = serverlessrepo.publish_application(packaged_template_str)
        codepipelinehelper.put_job_success(job_id, sar_response)
    except Exception as e:
        LOG.error(str(e))
        codepipelinehelper.put_job_failure(job_id, e)


def _remove_sensitive_items_from_event(event):
    """Remove sensitive items from the CodePipeline event.

    Arguments:
        event {dict} -- The JSON event sent to AWS Lambda by AWS CodePipeline

    Returns:
        dict -- The redacted CodePipeline event

    """
    event_to_log = copy.deepcopy(event)
    artifact_credentials = event_to_log['CodePipeline.job']['data']['artifactCredentials']
    artifact_credentials['accessKeyId'] = HIDDEN_VALUE
    artifact_credentials['secretAccessKey'] = HIDDEN_VALUE
    artifact_credentials['sessionToken'] = HIDDEN_VALUE

    return event_to_log
