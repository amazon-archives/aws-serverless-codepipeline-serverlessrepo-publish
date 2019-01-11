import pytest

from botocore.exceptions import ClientError
from serverlessrepo.exceptions import S3PermissionsRequired

import handler


@pytest.fixture
def mock_s3(mocker):
    mocker.patch.object(handler, 'S3')
    return handler.S3


@pytest.fixture
def mock_codepipeline(mocker):
    mocker.patch.object(handler, 'CODEPIPELINE')
    return handler.CODEPIPELINE


@pytest.fixture
def mock_serverlessrepo(mocker):
    mocker.patch.object(handler, 'serverlessrepo')
    return handler.serverlessrepo


def test_publish(mock_s3, mock_codepipeline, mock_serverlessrepo):
    mock_s3.get_object.return_value.get.return_value.read.return_value.decode.return_value = 'packaged_template_content'
    mock_serverlessrepo.publish_application.return_value = _mock_publish_application_response()
    mock_codepipeline.put_job_success_result.return_value = None

    handler.publish(_mock_codepipeline_event(), None)

    mock_s3.get_object.assert_called_once_with(
        Bucket='sample-pipeline-artifact-store-bucket',
        Key='sample-artifact-key'
    )
    mock_serverlessrepo.publish_application.assert_called_once_with('packaged_template_content')
    mock_codepipeline.put_job_success_result.assert_called_once_with(
        jobId='sample-codepipeline-job-id',
        executionDetails={
            'summary': str(_mock_publish_application_response()),
            'percentComplete': 100
        }
    )


def test_publish_unable_to_get_input_artifact(mock_s3, mock_codepipeline, mock_serverlessrepo):
    mock_s3.get_object.side_effect = ClientError(
        {
            "Error": {
                "Code": "AccessDenied",
                "Message": "Access Denied"
            }
        },
        "GetObject"
    )

    with pytest.raises(ClientError):
        handler.publish(_mock_codepipeline_event(), None)
    mock_s3.get_object.assert_called_once_with(
        Bucket='sample-pipeline-artifact-store-bucket',
        Key='sample-artifact-key'
    )
    mock_serverlessrepo.assert_not_called()
    mock_codepipeline.assert_not_called()


def test_publish_unsuccessful(mock_s3, mock_codepipeline, mock_serverlessrepo):
    mock_s3.get_object.return_value.get.return_value.read.return_value.decode.return_value = 'packaged_template_content'
    mock_serverlessrepo.publish_application.side_effect = S3PermissionsRequired(
        bucket='some-s3-bucket',
        key='some-s3-key'
    )
    mock_codepipeline.put_job_failure_result.return_value = None

    handler.publish(_mock_codepipeline_event(), None)
    mock_s3.get_object.assert_called_once_with(
        Bucket='sample-pipeline-artifact-store-bucket',
        Key='sample-artifact-key'
    )
    mock_serverlessrepo.publish_application.assert_called_once_with('packaged_template_content')
    mock_codepipeline.put_job_failure_result.assert_called_once_with(
        jobId='sample-codepipeline-job-id',
        failureDetails={
            'type': 'JobFailed',
            'message': str(S3PermissionsRequired(bucket='some-s3-bucket', key='some-s3-key'))
        }
    )
    mock_codepipeline.put_job_success_result.assert_not_called()


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
                                'objectKey': 'sample-artifact-key'
                            },
                            'type': 'S3'
                        },
                        'revision': None,
                        'name': 'sample-artifact-name'
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


def _mock_publish_application_response():
    return {
        'application_id': 'sample-application-id',
        'actions': ['CREATE_APPLICATION'],
        'details': {
            'Author': 'sample-author',
            'Description': 'sample-description',
            'Name': 'sample-app-name',
            'SemanticVersion': '1.0.0',
            'SourceCodeUrl': 'https://github.com/'}
    }
