"""S3 helper for getting the input artifact."""

import lambdalogging

import boto3
import zipfile
import io

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
    _validate_input_artifacts(input_artifacts)
    artifact_to_fetch = input_artifacts[0]

    artifact_s3_location = artifact_to_fetch['location']['s3Location']
    bucket = artifact_s3_location['bucketName']
    key = artifact_s3_location['objectKey']

    response = S3.get_object(Bucket=bucket, Key=key)
    LOG.info('%s/%s fetched. %s bytes.', bucket, key, response['ContentLength'])

    zipped_content_as_bytes = response.get('Body').read()
    return _unzip_as_string(zipped_content_as_bytes)


def _validate_input_artifacts(input_artifacts):
    """Validate the length of input artifacts list is 1.

    Arguments:
        input_artifacts {dict list} -- list of input artifacts
    """
    if len(input_artifacts) != 1:
        raise RuntimeError('You should only have one input artifact. Please check the setting for the action.')


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
