"""S3 helper for getting the input artifact."""

import lambdalogging

import boto3

LOG = lambdalogging.getLogger(__name__)

PACKAGED_TEMPLATE = 'PackagedTemplate'


def get_input_artifact(event):
    """Get the packaged SAM template from CodePipeline S3 Bucket.

    Arguments:
        event {dict} -- The JSON event sent to AWS Lambda by AWS CodePipeline

    Returns:
        str -- The content in the packaged SAM template as string

    """
    artifact_credentials = event['CodePipeline.job']['data']['artifactCredentials']
    S3 = boto3.client(
        's3',
        aws_access_key_id=artifact_credentials['accessKeyId'],
        aws_secret_access_key=artifact_credentials['secretAccessKey'],
        aws_session_token=artifact_credentials['sessionToken']
    )

    input_artifacts = event['CodePipeline.job']['data']['inputArtifacts']
    artifact_to_fetch = _find_artifact_in_list(input_artifacts)

    artifact_s3_location = artifact_to_fetch['location']['s3Location']
    bucket = artifact_s3_location['bucketName']
    key = artifact_s3_location['objectKey']

    response = S3.get_object(Bucket=bucket, Key=key)
    LOG.info('{}/{} fetched. {} bytes.', bucket, key, response['ContentLength'])
    return response.get('Body').read().decode(response['ContentLength'])


def _find_artifact_in_list(input_artifacts):
    """Find the artifact named 'PackagedTemplate' in the list of artifacts.

    Arguments:
        input_artifacts {dict list} -- list of input artifacts
        https://docs.aws.amazon.com/codepipeline/latest/APIReference/API_Artifact.html

    Raises:
        RuntimeError -- Raise error if not able to find the artifact

    Returns:
        dict -- artifact to fetch from S3

    """
    for artifact in input_artifacts:
        if artifact['name'] == PACKAGED_TEMPLATE:
            return artifact

    raise RuntimeError('Unable to find the artifact with name ' + PACKAGED_TEMPLATE)
