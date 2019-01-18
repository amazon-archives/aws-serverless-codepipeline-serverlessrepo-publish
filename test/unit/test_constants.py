"""Constants used for unit tests."""
import json
import os


def generate_pipeline_event(input_artifacts):
    """Generate mock pipeline event based on the input artifacts.

    Arguments:
        input_artifacts {dict list} -- list of input artifacts

    Returns:
        dict -- mock pipeline event based on the input artifacts

    """
    full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testdata', 'codepipeline_event.json')

    with open(full_path) as f:
        event = json.load(f)

    event['CodePipeline.job']['data']['inputArtifacts'] = input_artifacts
    return event


mock_codepipeline_event = generate_pipeline_event(
    [
        {
            "location": {
                "s3Location": {
                    "bucketName": "sample-pipeline-artifact-store-bucket",
                    "objectKey": "sample-artifact-key1"
                },
                "type": "S3"
            },
            "revision": None,
            "name": "NotPackagedTemplate"
        },
        {
            "location": {
                "s3Location": {
                    "bucketName": "sample-pipeline-artifact-store-bucket",
                    "objectKey": "sample-artifact-key"
                },
                "type": "S3"
            },
            "revision": None,
            "name": "PackagedTemplate"
        }
    ]
)
mock_codepipeline_event_no_artifact_found = generate_pipeline_event(
    [
        {
            "location": {
                "s3Location": {
                    "bucketName": "sample-pipeline-artifact-store-bucket",
                    "objectKey": "sample-artifact-key1"
                },
                "type": "S3"
            },
            "revision": None,
            "name": "NotPackagedTemplate"
        }
    ]
)
