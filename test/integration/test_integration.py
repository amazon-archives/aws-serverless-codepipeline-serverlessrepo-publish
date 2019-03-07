"""Integration test for CodePipeline ServerlessRepo Publish app."""
import pytest
import uuid
import time
import boto3
import os
import logging


SOURCE_BUCKET_CACHE_KEY = 'source_bucket'
ARTIFACT_STORE_BUCKET_CACHE_KEY = 'artifact_store_bucket'
TEST_APPLICATION_ID_CACHE_KEY = 'test_application_id'
PUBLISH_APPLICATION_ID_CACHE_KEY = 'publish_application_id'
CODEPIPELINE_NAME_CACHE_KEY = 'codepipeline_name'
TEST_APPLICATION_NAME = 'my-sam-app'
PACKAGE_BUCKET = 'codepipeline-sar-publish-integ-tests'
PUBLISH_APPLICATION_TEMPLATE_KEY = 'template.yml'
PUBLISH_APPLICATION_ARN_REPLACE_STR = "${PUBLISH_APP_ARN}"
APPLICATION_ID_FORMAT = 'arn:aws:serverlessrepo:{}:{}:applications/{}'
PUBLISH_APPLICATION_NAME = 'codepipeline-serverlessrepo-publish-app-{}'.format(str(uuid.uuid4()))
AWS_REGION = os.environ['AWS_REGION']
AWS_ACCOUNT_ID = os.environ['AWS_ACCOUNT_ID']
TEST_APPLICATION_ID = APPLICATION_ID_FORMAT.format(AWS_REGION, AWS_ACCOUNT_ID, TEST_APPLICATION_NAME)
PUBLISH_APPLICATION_ID = APPLICATION_ID_FORMAT.format(AWS_REGION, AWS_ACCOUNT_ID, PUBLISH_APPLICATION_NAME)
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
LOG = logging.getLogger(__name__)

CLOUDFORMATION_CLIENT = boto3.client('cloudformation')
SAR_CLIENT = boto3.client('serverlessrepo')
S3_RESOURCE = boto3.resource('s3')
CODEPIPELINE_CLIENT = boto3.client('codepipeline')


@pytest.fixture(scope='module', autouse=True)
def setup_and_teardown(request):
    def teardown():
        try:
            _empty_bucket(request.config.cache.get(ARTIFACT_STORE_BUCKET_CACHE_KEY, ''))
        except Exception as e:
            LOG.warning('Exception when emptying the CodePipeline artifact store bucket=%s', e)

        try:
            _empty_bucket(request.config.cache.get(SOURCE_BUCKET_CACHE_KEY, ''))
        except Exception as e:
            LOG.warning('Exception when emptying the CodePipeline source bucket=%s', e)

        try:
            CLOUDFORMATION_CLIENT.delete_stack(StackName=test_env_stack_name)
        except Exception as e:
            LOG.warning('Exception when deleting the test environment stack=%s', e)

        try:
            SAR_CLIENT.delete_application(ApplicationId=TEST_APPLICATION_ID)
        except Exception as e:
            LOG.warning('Exception when deleting the test application in SAR=%s', e)

        try:
            SAR_CLIENT.delete_application(ApplicationId=PUBLISH_APPLICATION_ID)
        except Exception as e:
            LOG.warning('Exception when deleting the SAR auto publish application in SAR=%s', e)

        LOG.info('Teardown complete')

    request.addfinalizer(teardown)

    SAR_CLIENT.create_application(
            Author='John Smith',
            Description='This serverless application publishes applications to AWS SAR',
            HomePageUrl='https://github.com',
            Name=PUBLISH_APPLICATION_NAME,
            SemanticVersion='0.0.1',
            TemplateUrl='https://s3.amazonaws.com/{}/{}'.format(PACKAGE_BUCKET, PUBLISH_APPLICATION_TEMPLATE_KEY)
    )

    test_env_stack_name = 'test-env-stack-' + str(uuid.uuid4())
    with open(os.path.join(CURRENT_DIRECTORY, 'test_environment.yml')) as test_environment_template:
        processed_test_environment_str = test_environment_template.read().replace(
            PUBLISH_APPLICATION_ARN_REPLACE_STR, PUBLISH_APPLICATION_ID
        )
    create_stack_result = CLOUDFORMATION_CLIENT.create_stack(
        StackName=test_env_stack_name,
        TemplateBody=processed_test_environment_str,
        Capabilities=['CAPABILITY_IAM', 'CAPABILITY_AUTO_EXPAND']
    )
    test_environment_stack_id = create_stack_result['StackId']

    stack_create_complete_waiter = CLOUDFORMATION_CLIENT.get_waiter('stack_create_complete')
    stack_create_complete_waiter.wait(
        StackName=test_environment_stack_id,
        WaiterConfig={
            'Delay': 10,
            'MaxAttempts': 60
        }
    )

    stack_resource_summaries = CLOUDFORMATION_CLIENT.list_stack_resources(
        StackName=test_environment_stack_id
    ).get('StackResourceSummaries')

    request.config.cache.set(SOURCE_BUCKET_CACHE_KEY, list(filter(
        lambda s: s['LogicalResourceId'] == 'SourceBucket', stack_resource_summaries
    ))[0].get('PhysicalResourceId'))
    request.config.cache.set(ARTIFACT_STORE_BUCKET_CACHE_KEY, list(filter(
        lambda s: s['LogicalResourceId'] == 'ArtifactStoreBucket', stack_resource_summaries
    ))[0].get('PhysicalResourceId'))
    request.config.cache.set(CODEPIPELINE_NAME_CACHE_KEY, list(filter(
        lambda s: s['LogicalResourceId'] == 'Pipeline', stack_resource_summaries
    ))[0].get('PhysicalResourceId'))

    try:
        SAR_CLIENT.delete_application(ApplicationId=TEST_APPLICATION_ID)
    except SAR_CLIENT.exceptions.NotFoundException as e:
        LOG.info('Application my-sam-app has already been deleted, ready for integ test to start=%s', e)
    LOG.info('Setup complete')


def test_end_to_end(request):
    test_source_zip_path = os.path.join(CURRENT_DIRECTORY, 'testdata', 'testapp.zip')
    _upload_source_zip_to_s3(request.config.cache.get(SOURCE_BUCKET_CACHE_KEY, ''), test_source_zip_path)

    execution_id = CODEPIPELINE_CLIENT.start_pipeline_execution(
        name=request.config.cache.get(CODEPIPELINE_NAME_CACHE_KEY, '')
    ).get('pipelineExecutionId')

    end_time = time.time() + 300
    while time.time() < end_time:
        try:
            if _pipeline_execution_failed(request.config.cache.get(CODEPIPELINE_NAME_CACHE_KEY, ''), execution_id):
                raise RuntimeError('Pipeline execution failed')
            SAR_CLIENT.get_application(ApplicationId=TEST_APPLICATION_ID, SemanticVersion='0.0.1')
            break
        except (
            SAR_CLIENT.exceptions.NotFoundException, CODEPIPELINE_CLIENT.exceptions.PipelineExecutionNotFoundException
        ):
            time.sleep(10)

    get_application_result = SAR_CLIENT.get_application(ApplicationId=TEST_APPLICATION_ID, SemanticVersion='0.0.1')
    assert get_application_result['Author'] == 'John Smith'
    assert get_application_result['Description'] == 'This serverless application is a new demo'
    assert get_application_result['Version']['SemanticVersion'] == '0.0.1'
    assert get_application_result['Version']['TemplateUrl'] is not None


def _upload_source_zip_to_s3(bucket_name, path):
    if bucket_name == '':
        raise RuntimeError('Unable to get source bucket name from cache')

    bucket = S3_RESOURCE.Bucket(bucket_name)
    bucket.upload_file(Filename=path, Key='testapp.zip')


def _empty_bucket(bucket_name):
    bucket = S3_RESOURCE.Bucket(bucket_name)
    bucket.object_versions.all().delete()


def _pipeline_execution_failed(name, execution_id):
    if name == '':
        raise RuntimeError('Unable to get pipeline name from cache')

    return CODEPIPELINE_CLIENT.get_pipeline_execution(
                pipelineName=name,
                pipelineExecutionId=execution_id
            ).get('pipelineExecution', {}).get('status') == 'Failed'
