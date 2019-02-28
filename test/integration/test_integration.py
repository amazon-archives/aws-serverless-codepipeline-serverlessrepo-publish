"""Integration test for CodePipeline ServerlessRepo Publish app."""
import pytest
import uuid
import time
import boto3
import os
import logging

SOURCE_BUCKET = 'source_bucket'
APPLICATION_ID = 'application_id'
APPLICATION_NAME = 'my-sam-app'
STACK_SUFFIX = str(uuid.uuid4())
CLOUDFORMATION_CLIENT = boto3.client('cloudformation')
SAR_CLIENT = boto3.client('serverlessrepo')
LOG = logging.getLogger(__name__)


@pytest.fixture(scope='module', autouse=True)
def setup_and_teardown(request):
    test_env_stack_name = 'test-env-stack-' + STACK_SUFFIX
    create_stack_result = CLOUDFORMATION_CLIENT.create_stack(
        StackName=test_env_stack_name,
        TemplateURL='https://s3.amazonaws.com/codepipeline-sar-publish-integ-tests/test_environment.yml',
        Parameters=[
            {
                'ParameterKey': 'AppTemplateURL',
                'ParameterValue': 'https://s3.amazonaws.com/codepipeline-sar-publish-integ-tests/template.yml'
            }
        ],
        Capabilities=['CAPABILITY_IAM', 'CAPABILITY_AUTO_EXPAND']
    )
    test_environment_stack_id = create_stack_result['StackId']

    _wait_until((CLOUDFORMATION_CLIENT.describe_stacks(
        StackName=test_environment_stack_id))['Stacks'][0]['StackStatus'] == 'CREATE_COMPLETE'
    )
    describe_stacks_result = CLOUDFORMATION_CLIENT.describe_stacks(StackName=test_environment_stack_id)
    test_environment_stack_outputs = describe_stacks_result['Stacks'][0]['Outputs']
    request.config.cache.set(SOURCE_BUCKET, filter(
        lambda o: o['OutputKey'] == 'SourceBucketName', test_environment_stack_outputs
    ).get('OutputValue'))

    try:
        SAR_CLIENT.delete_application(_get_application_id())
    except Exception:
        LOG.info('Application has already been deleted, ready for integ test to start')

    def teardown():
        CLOUDFORMATION_CLIENT.delete_stack(StackName=test_env_stack_name)
        SAR_CLIENT.delete_application(ApplicationId=request.config.cache.get(APPLICATION_ID))
    request.addfinalizer(teardown)


def test_end_to_end(request):
    integration_folder_path = os.path.dirname(os.path.abspath(__file__))
    test_source_files_path = os.path.join(integration_folder_path, 'testdata')
    _upload_source_files_to_s3(request.config.cache.get(SOURCE_BUCKET), test_source_files_path)

    # give some time for the change to go through integ test pipeline and then publish to SAR
    time.sleep(180)

    application_id = _get_application_id()
    request.config.cache.set(APPLICATION_ID, application_id)
    get_application_result = SAR_CLIENT.get_application(ApplicationId=application_id)
    assert get_application_result['Author'] == 'John Smith'
    assert get_application_result['Description'] == 'This serverless application is a new demo'
    assert get_application_result['SpdxLicenseId'] == 'MIT'
    assert get_application_result['Version']['SemanticVersion'] == '0.0.1'


def _wait_until(predicate, timeout=300, period=1):
    end_time = time.time() + timeout
    while time.time() < end_time:
        if predicate:
            return
        time.sleep(period)
    raise RuntimeError('Time out')


def _upload_source_files_to_s3(bucket_name, path):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)

    for subdir, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(subdir, file)
            with open(full_path, 'rb') as data:
                bucket.put_object(Key=full_path[len(path) + 1:], Body=data)


def _get_application_id():
    list_applications_result = SAR_CLIENT.list_applications()
    return filter(
        lambda a: a['Name'] == APPLICATION_NAME, list_applications_result['Applications']
    ).get('ApplicationId')
