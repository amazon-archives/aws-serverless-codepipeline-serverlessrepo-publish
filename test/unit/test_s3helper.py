"""Unit test for handler.py."""
import pytest
from mock import MagicMock

from botocore.exceptions import ClientError

import s3helper
from test_constants import (
    mock_codepipeline_event,
    mock_codepipeline_event_more_than_one_input_artifacts,
    mock_codepipeline_event_no_input_artifacts
)


@pytest.fixture
def mock_boto3(mocker):
    mocker.patch.object(s3helper, 'boto3')
    return s3helper.boto3


@pytest.fixture
def mock_zipfile(mocker):
    mocker.patch.object(s3helper, 'zipfile')
    return s3helper.zipfile


def test_get_input_artifact(mock_boto3, mock_zipfile):
    zipped_content_as_bytes = b'zipped_packaged_template_content'
    expected_result = 'packaged_template_content'

    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3
    mock_s3.get_object.return_value.get.return_value.read.return_value = zipped_content_as_bytes
    mock_zipfile_object = MagicMock()
    mock_zipfile.ZipFile.return_value = mock_zipfile_object
    mock_zipfile_object.read.return_value = bytes(expected_result, encoding='utf-8')

    assert s3helper.get_input_artifact(mock_codepipeline_event) == expected_result

    mock_s3.get_object.assert_called_once_with(
        Bucket='sample-pipeline-artifact-store-bucket',
        Key='sample-artifact-key'
    )


def test_get_input_artifact_more_than_one_input_artifacts(mock_boto3, mock_zipfile):
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3

    with pytest.raises(
        RuntimeError,
        match='You should only have one input artifact. Please check the setting for the action.'
    ):
        s3helper.get_input_artifact(mock_codepipeline_event_more_than_one_input_artifacts)

    mock_s3.get_object.assert_not_called()
    mock_zipfile.assert_not_called()


def test_get_input_artifact_no_input_artifacts(mock_boto3, mock_zipfile):
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3

    with pytest.raises(
        RuntimeError,
        match='You should only have one input artifact. Please check the setting for the action.'
    ):
        s3helper.get_input_artifact(mock_codepipeline_event_no_input_artifacts)

    mock_s3.get_object.assert_not_called()
    mock_zipfile.assert_not_called()


def test_get_input_artifact_unable_to_get_artifact(mock_boto3, mock_zipfile):
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
        s3helper.get_input_artifact(mock_codepipeline_event)
    assert 'Access Denied' in str(excinfo.value)

    mock_s3.get_object.assert_called_once_with(
        Bucket='sample-pipeline-artifact-store-bucket',
        Key='sample-artifact-key'
    )
    mock_zipfile.assert_not_called()
