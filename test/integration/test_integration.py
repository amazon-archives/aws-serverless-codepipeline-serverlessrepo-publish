"""Integration test for CodePipeline ServerlessRepo Publish app."""
import pytest
import uuid
import time
import boto3
import os
import logging


SOURCE_BUCKET_CACHE_KEY = 'source_bucket'
TEST_APPLICATION_ID_CACHE_KEY = 'test_application_id'
PUBLISH_APPLICATION_ID_CACHE_KEY = 'publish_application_id'
TEST_APPLICATION_NAME = 'my-sam-app'
PUBLISH_APPLICATION_NAME = 'codepipeline-serverlessrepo-publish-app-integ-test-only'
STACK_SUFFIX = str(uuid.uuid4())
CLOUDFORMATION_CLIENT = boto3.client('cloudformation')
SAR_CLIENT = boto3.client('serverlessrepo')
LOG = logging.getLogger(__name__)


@pytest.fixture(scope='module', autouse=True)
def setup_and_teardown(request):
    # try:
    SAR_CLIENT.create_application(
            Author='John Smith',
            Description='This serverless application publishes applications to AWS Serverless Application Repository',
            HomePageUrl='https://github.com',
            Name=PUBLISH_APPLICATION_NAME,
            SemanticVersion='0.0.1',
            TemplateUrl='https://s3.amazonaws.com/codepipeline-sar-publish-integ-tests/template.yml'
    )
    # except Exception:
    #  LOG.info('Application codepipeline-serverlessrepo-publish-integ-test-only already exists, ready for integ test')

    request.config.cache.set(PUBLISH_APPLICATION_ID_CACHE_KEY, _get_application_id(PUBLISH_APPLICATION_NAME))
    _wait_until(
        SAR_CLIENT.get_application(
            ApplicationId=request.config.cache.get(PUBLISH_APPLICATION_ID_CACHE_KEY)
        ).get('Version') is not None
    )

    test_env_stack_name = 'test-env-stack-' + STACK_SUFFIX
    create_stack_result = CLOUDFORMATION_CLIENT.create_stack(
        StackName=test_env_stack_name,
        TemplateURL='https://s3.amazonaws.com/codepipeline-sar-publish-integ-tests/test_environment.yml',
        Capabilities=['CAPABILITY_IAM', 'CAPABILITY_AUTO_EXPAND']
    )
    test_environment_stack_id = create_stack_result['StackId']

    _wait_until((CLOUDFORMATION_CLIENT.describe_stacks(
        StackName=test_environment_stack_id))['Stacks'][0]['StackStatus'] == 'CREATE_COMPLETE'
    )
    describe_stacks_result = CLOUDFORMATION_CLIENT.describe_stacks(StackName=test_environment_stack_id)
    test_environment_stack_outputs = describe_stacks_result['Stacks'][0]['Outputs']
    request.config.cache.set(SOURCE_BUCKET_CACHE_KEY, filter(
        lambda o: o['OutputKey'] == 'SourceBucketName', test_environment_stack_outputs
    ).get('OutputValue'))

    try:
        SAR_CLIENT.delete_application(_get_application_id(TEST_APPLICATION_NAME))
    except Exception:
        LOG.info('Application my-sam-app has already been deleted, ready for integ test to start')

    def teardown():
        CLOUDFORMATION_CLIENT.delete_stack(StackName=test_env_stack_name)
        SAR_CLIENT.delete_application(ApplicationId=request.config.cache.get(TEST_APPLICATION_ID_CACHE_KEY))
        SAR_CLIENT.delete_application(ApplicationId=request.config.cache.get(PUBLISH_APPLICATION_ID_CACHE_KEY))
    request.addfinalizer(teardown)


def test_end_to_end(request):
    integration_folder_path = os.path.dirname(os.path.abspath(__file__))
    test_source_files_path = os.path.join(integration_folder_path, 'testdata')
    _upload_source_files_to_s3(request.config.cache.get(SOURCE_BUCKET_CACHE_KEY), test_source_files_path)

    _wait_until(SAR_CLIENT.list_applications().get('Applications') != [], timeout=180, period=10)

    application_id = _get_application_id(TEST_APPLICATION_NAME)
    request.config.cache.set(TEST_APPLICATION_ID_CACHE_KEY, application_id)
    get_application_result = SAR_CLIENT.get_application(ApplicationId=application_id)
    assert get_application_result['Author'] == 'John Smith'
    assert get_application_result['Description'] == 'This serverless application is a new demo'
    assert get_application_result['SpdxLicenseId'] == 'MIT'
    assert _are_lists_equal(get_application_result['Labels'], ['serverless']) is True
    assert get_application_result['HomePageUrl'] == 'https://github.com/johnsmith/my-sam-app'
    assert get_application_result['ReadmeUrl'] is not None
    assert get_application_result['LicenseUrl'] is not None
    assert get_application_result['Version']['SemanticVersion'] == '0.0.1'
    assert get_application_result['Version']['SourceCodeUrl'] == 'https://github.com/johnsmith/my-sam-app'
    assert get_application_result['Version']['TemplateUrl'] is not None


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


def _get_application_id(application_name):
    list_applications_result = SAR_CLIENT.list_applications()
    return filter(
        lambda a: a['Name'] == application_name, list_applications_result['Applications']
    ).get('ApplicationId')


def _are_lists_equal(l1, l2):
    return len(l1) == len(l2) and sorted(l1) == sorted(l2)
