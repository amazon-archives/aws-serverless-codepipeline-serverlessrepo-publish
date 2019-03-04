"""S3 helper for getting the input artifact."""

import lambdalogging

import boto3
import zipfile
import io
import os


LOG = lambdalogging.getLogger(__name__)


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
    LOG.info('%s/%s fetched. %s bytes.', bucket, key, response['ContentLength'])

    zipped_content_as_bytes = response.get('Body').read()
    return _unzip_as_string(zipped_content_as_bytes)


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
    input_artifact_to_use = os.environ['INPUT_ARTIFACT']
    for artifact in input_artifacts:
        if artifact['name'] == input_artifact_to_use:
            return artifact

    raise RuntimeError('Unable to find the input artifact with name ' + input_artifact_to_use)


def _unzip_as_string(data):
    """Unzip stream of data in bytes as string.

    Arguments:
        data {bytes} -- Zipped data as bytes

    Returns:
        str -- Unzipped data as string

    """
    z = zipfile.ZipFile(io.BytesIO(data))
    unzipped_data = z.read(z.infolist()[0])
    return unzipped_data.decode()
