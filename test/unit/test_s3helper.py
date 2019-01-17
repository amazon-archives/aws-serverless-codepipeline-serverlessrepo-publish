"""Unit test for handler.py."""
import pytest
from mock import MagicMock

from botocore.exceptions import ClientError

import s3helper


@pytest.fixture
def mock_boto3(mocker):
    mocker.patch.object(s3helper, 'boto3')
    return s3helper.boto3


def test_get_input_artifact(mock_boto3):
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3
    mock_s3.get_object.return_value.get.return_value.read.return_value.decode.return_value = 'packaged_template_content'

    s3helper.get_input_artifact(_mock_codepipeline_event())

    mock_s3.get_object.assert_called_once_with(
        Bucket='sample-pipeline-artifact-store-bucket',
        Key='sample-artifact-key'
    )


def test_get_input_artifact_unable_to_find_artifact(mock_boto3):
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3

    with pytest.raises(RuntimeError, match='Unable to find the artifact with name ' + s3helper.PACKAGED_TEMPLATE):
        s3helper.get_input_artifact(_mock_codepipeline_event_no_artifact_found())

    mock_s3.get_object.assert_not_called()


def test_get_input_artifact_unable_to_get_artifact(mock_boto3):
    exception_thrown = ClientError(
        {
            "Error": {
                "Code": "AccessDenied",
                "Message": "Access Denied"
            }
        },
        "GetObject"
    )
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3
    mock_s3.get_object.side_effect = exception_thrown

    with pytest.raises(ClientError) as excinfo:
        s3helper.get_input_artifact(_mock_codepipeline_event())
    assert 'Access Denied' in str(excinfo.value)

    mock_s3.get_object.assert_called_once_with(
        Bucket='sample-pipeline-artifact-store-bucket',
        Key='sample-artifact-key'
    )


def _mock_codepipeline_event():
    return {
        'CodePipeline.job': {
            'id': 'sample-codepipeline-job-id',
            'accountId': 'sample-account-id',
            'data': {
                'actionConfiguration': {
                    'configuration': {
                        'FunctionName': 'sample-lambda-function-name',
                        'UserParameters': 'sample-user-parameter'
                    }
                },
                'inputArtifacts': [
                    {
                        'location': {
                            's3Location': {
                                'bucketName': 'sample-pipeline-artifact-store-bucket',
                                'objectKey': 'sample-artifact-key1'
                            },
                            'type': 'S3'
                        },
                        'revision': None,
                        'name': 'NotPackagedTemplate'
                    },
                    {
                        'location': {
                            's3Location': {
                                'bucketName': 'sample-pipeline-artifact-store-bucket',
                                'objectKey': 'sample-artifact-key'
                            },
                            'type': 'S3'
                        },
                        'revision': None,
                        'name': 'PackagedTemplate'
                    }
                ],
                'outputArtifacts': [],
                'artifactCredentials': {
                    'secretAccessKey': 'sample-secret-access-key',
                    'sessionToken': 'sample-session-token',
                    'accessKeyId': 'sample-access-key-id'
                },
                'continuationToken': 'sample-continuation-token'
            }
        }
    }


def _mock_codepipeline_event_no_artifact_found():
    return {
        'CodePipeline.job': {
            'id': 'sample-codepipeline-job-id',
            'accountId': 'sample-account-id',
            'data': {
                'actionConfiguration': {
                    'configuration': {
                        'FunctionName': 'sample-lambda-function-name',
                        'UserParameters': 'sample-user-parameter'
                    }
                },
                'inputArtifacts': [
                    {
                        'location': {
                            's3Location': {
                                'bucketName': 'sample-pipeline-artifact-store-bucket',
                                'objectKey': 'sample-artifact-key1'
                            },
                            'type': 'S3'
                        },
                        'revision': None,
                        'name': 'NotPackagedTemplate'
                    }
                ],
                'outputArtifacts': [],
                'artifactCredentials': {
                    'secretAccessKey': 'sample-secret-access-key',
                    'sessionToken': 'sample-session-token',
                    'accessKeyId': 'sample-access-key-id'
                },
                'continuationToken': 'sample-continuation-token'
            }
        }
    }
