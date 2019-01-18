"""Unit test for handler.py."""
import pytest

from botocore.exceptions import ClientError
from serverlessrepo.exceptions import S3PermissionsRequired

import handler
from test_constants import mock_codepipeline_event, mock_codepipeline_event_no_artifact_found
from s3helper import PACKAGED_TEMPLATE


@pytest.fixture
def mock_s3helper(mocker):
    mocker.patch.object(handler, 's3helper')
    return handler.s3helper


@pytest.fixture
def mock_codepipelinehelper(mocker):
    mocker.patch.object(handler, 'codepipelinehelper')
    return handler.codepipelinehelper


@pytest.fixture
def mock_serverlessrepo(mocker):
    mocker.patch.object(handler, 'serverlessrepo')
    return handler.serverlessrepo


def test_publish(mock_s3helper, mock_codepipelinehelper, mock_serverlessrepo):
    mock_s3helper.get_input_artifact.return_value = 'packaged_template_content'
    mock_serverlessrepo.publish_application.return_value = _mock_publish_application_response()
    mock_codepipelinehelper.put_job_success.return_value = None

    handler.publish(mock_codepipeline_event, None)

    mock_s3helper.get_input_artifact.assert_called_once_with(mock_codepipeline_event)
    mock_serverlessrepo.publish_application.assert_called_once_with('packaged_template_content')
    mock_codepipelinehelper.put_job_success.assert_called_once_with(
        'sample-codepipeline-job-id',
        _mock_publish_application_response()
    )


def test_publish_unable_to_find_artifact(mock_s3helper, mock_codepipelinehelper, mock_serverlessrepo):
    exception_thrown = RuntimeError('Unable to find the artifact with name ' + PACKAGED_TEMPLATE)
    mock_s3helper.get_input_artifact.side_effect = exception_thrown

    handler.publish(mock_codepipeline_event_no_artifact_found, None)

    mock_s3helper.get_input_artifact.assert_called_once_with(mock_codepipeline_event_no_artifact_found)
    mock_serverlessrepo.assert_not_called()
    mock_codepipelinehelper.put_job_failure.assert_called_once_with(
        'sample-codepipeline-job-id',
        exception_thrown
    )
    mock_codepipelinehelper.put_job_success.assert_not_called()


def test_publish_unable_to_get_input_artifact(mock_s3helper, mock_codepipelinehelper, mock_serverlessrepo):
    exception_thrown = ClientError(
        {
            "Error": {
                "Code": "AccessDenied",
                "Message": "Access Denied"
            }
        },
        "GetObject"
    )
    mock_s3helper.get_input_artifact.side_effect = exception_thrown

    handler.publish(mock_codepipeline_event, None)

    mock_s3helper.get_input_artifact.assert_called_once_with(mock_codepipeline_event)
    mock_serverlessrepo.assert_not_called()
    mock_codepipelinehelper.put_job_failure.assert_called_once_with(
        'sample-codepipeline-job-id',
        exception_thrown
    )
    mock_codepipelinehelper.put_job_success_result.assert_not_called()


def test_publish_unsuccessful(mock_s3helper, mock_codepipelinehelper, mock_serverlessrepo):
    exception_thrown = S3PermissionsRequired(
        bucket='some-s3-bucket',
        key='some-s3-key'
    )
    mock_s3helper.get_input_artifact.return_value = 'packaged_template_content'
    mock_serverlessrepo.publish_application.side_effect = exception_thrown
    mock_codepipelinehelper.put_job_failure.return_value = None

    handler.publish(mock_codepipeline_event, None)

    mock_s3helper.get_input_artifact.assert_called_once_with(mock_codepipeline_event)
    mock_serverlessrepo.publish_application.assert_called_once_with('packaged_template_content')
    mock_codepipelinehelper.put_job_failure.assert_called_once_with(
        'sample-codepipeline-job-id',
        exception_thrown
    )
    mock_codepipelinehelper.put_job_success.assert_not_called()


def _mock_publish_application_response():
    return {
        'application_id': 'sample-application-id',
        'actions': ['CREATE_APPLICATION'],
        'details': {
            'Author': 'sample-author',
            'Description': 'sample-description',
            'Name': 'sample-app-name',
            'SemanticVersion': '1.0.0',
            'SourceCodeUrl': 'https://github.com/'
        }
    }
