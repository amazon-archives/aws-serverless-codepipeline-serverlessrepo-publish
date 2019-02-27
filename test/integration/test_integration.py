"""Integration test for CodePipeline ServerlessRepo Publish app."""
import pytest
import uuid
import time

import boto3
import os

REGION = 'us-east-1'
STACK_SUFFIX = str(uuid.uuid4())
CLOUDFORMATION_CLIENT = boto3.client('cloudformation', region_name=REGION)
S3_CLIENT = boto3.client('s3', region_name=REGION)


@pytest.fixture(scope='module', autouse=True)
def setup_and_teardown(request):
    create_stack_result = CLOUDFORMATION_CLIENT.create_stack(
        StackName='test-env-stack-' + STACK_SUFFIX,
        TemplateURL='https://s3.amazonaws.com/codepipeline-sar-publish-integ-tests/test_environment.yml',
        Parameters=[
            {
                'ParameterKey': 'AppTemplateURL',
                'ParameterValue': 'https://s3.amazonaws.com/codepipeline-sar-publish-integ-tests/template.yml'
            }
        ],
        Capabilities=['CAPABILITY_IAM', 'CAPABILITY_AUTO_EXPAND']
    )
    # test_environment_stack_id = create_stack_result['StackId']

    # wait_until((CLOUDFORMATION_CLIENT.describe_stacks(
    #     StackName=test_environment_stack_id))['Stacks'][0]['StackStatus'] == 'CREATE_COMPLETE'
    # )
    # describe_stacks_result = CLOUDFORMATION_CLIENT.describe_stacks(StackName=test_environment_stack_id)
    # test_environment_stack_outputs = describe_stacks_result['Stacks'][0]['Outputs']
    # print(test_environment_stack_outputs)

    print('=========test finish===========')

# def teardown():
#     # tear down here
#     print('\ntear down')
# request.addfinalizer(teardown)


# def test_end_to_end():
#     # S3_CLIENT.put_object('')


# def wait_until(predicate, timeout=300, period=1):
#     end_time = time.time() + timeout
#     while time.time() < end_time:
#         if predicate:
#             return True
#         time.sleep(period)
#     raise RuntimeError('Time out')
