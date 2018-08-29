## AWS Serverless Codepipeline Serverlessrepo Publish ![Build Status](https://codebuild.us-east-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoiRWVJS0x2ZFJGMTJYZWVKWHRxZXQzV3dHYlM4enJPc3k3bno4cmZRMmtwQkR5dGRSYUp1bDF3bnNHUE1NV1JpTHpTWC9KZ1Q4YmhtcG5aOXdNVWd4U2ZBPSIsIml2UGFyYW1ldGVyU3BlYyI6IlVhNGJ2dXlnZG1kbHJLS2siLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=master)

This is a serverless app that publishes applications to AWS Serverless Application Repository. This app creates a Lambda function that a user could then use as an Invoke action target in their CodePipeline.

## Architecture

![App Architecture](https://github.com/awslabs/aws-serverless-codepipeline-serverlessrepo-publish/raw/master/app-architecture.png)

1. App has a single Lambda function ServerlessRepoPublish lambda.
1. ServerlessRepoPublish lambda is invoked by CodePipeline as part of the Invoke Action of a pipeline.
1. ServerlessRepoPublish lambda is passed the S3 URL of the packaged SAM template in the CodePipeline S3 bucket.
1. ServerlessRepoPublish lambda downloads the template and parses its Metadata to get application information for calls to CreateApplication/UpdateApplication. 
1. ServerlessRepoPublish lambda then does the create or update job processor logic:
   1. Call [AcknowledgeJob](https://docs.aws.amazon.com/codepipeline/latest/APIReference/API_AcknowledgeJob.html) API to claim the job.
   1. Read SAM template and parse application metadata.
   1. Call [CreateApplication](https://docs.aws.amazon.com/serverlessrepo/latest/devguide/applications.html) API with metadata and pass SAM template with semantic version from template metadata.
   1. If success, call [PutJobSuccessResult](https://docs.aws.amazon.com/codepipeline/latest/APIReference/API_PutJobSuccessResult.html)
   1. If application already exists
      1. Call [GetApplication](https://docs.aws.amazon.com/serverlessrepo/latest/devguide/applications-applicationid.html) - Application ARN can be parsed from the 4xx error message. NOTE: This isn't the cleanest solution, but it doesn't require an API change to SAR.
      1. Call [UpdateApplication](https://docs.aws.amazon.com/serverlessrepo/latest/devguide/applications-applicationid.html) if any metadata has changed
      1. Call [CreateApplicationVersion](https://docs.aws.amazon.com/serverlessrepo/latest/devguide/applications-applicationid-versions-semanticversion.html) with SAM template. If it already exists, do nothing.
   1. If API calls fail for any other reason, call [PutJobFailureResult](https://docs.aws.amazon.com/codepipeline/latest/APIReference/API_PutJobFailureResult.html) with failure details.

## License Summary

This sample code is made available under the MIT license. 
