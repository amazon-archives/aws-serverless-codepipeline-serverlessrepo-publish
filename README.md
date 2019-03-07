## AWS Serverless Codepipeline Serverlessrepo Publish ![Build Status](https://codebuild.us-east-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoiRWVJS0x2ZFJGMTJYZWVKWHRxZXQzV3dHYlM4enJPc3k3bno4cmZRMmtwQkR5dGRSYUp1bDF3bnNHUE1NV1JpTHpTWC9KZ1Q4YmhtcG5aOXdNVWd4U2ZBPSIsIml2UGFyYW1ldGVyU3BlYyI6IlVhNGJ2dXlnZG1kbHJLS2siLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=master)

This is a serverless app that publishes applications to AWS Serverless Application Repository (SAR). This app contains a Lambda function that a user can then use as an Invoke action target in their CodePipeline. To use this app, please refer to the tutorial [here](https://docs.aws.amazon.com/codepipeline/latest/userguide/tutorials-serverlessrepo-auto-publish.html).

## Architecture

![App Architecture](https://github.com/awslabs/aws-serverless-codepipeline-serverlessrepo-publish/raw/master/app-architecture.png)

1. App has a single Lambda function ServerlessRepoPublish lambda. It uses convenience helpers from the [serverlessrepo](https://pypi.org/project/serverlessrepo/) python module to publish applications to SAR.
2. ServerlessRepoPublish lambda is invoked by CodePipeline as part of the Invoke Action of a pipeline.
   1. ServerlessRepoPublish lambda is invoked with the [CodePipeline JSON event](https://docs.aws.amazon.com/codepipeline/latest/userguide/actions-invoke-lambda-function.html#actions-invoke-lambda-function-json-event-example) and then gets the S3 location of the packaged SAM template in the event.
   2. It gets the packaged SAM template from CodePipeline S3 bucket
   3. It calls serverlessrepo.publish_application() with the packaged template. This call will first parse the [Metadata section](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-template-publishing-applications-metadata-properties.html) of the template and then make corresponding API calls to SAR. Below is the code logic done in serverlessrepo.publish_application():
      1. Parse the Metadata section of the packaged SAM template and get the application metadata
      2. Call SAR [CreateApplication](https://docs.aws.amazon.com/cli/latest/reference/serverlessrepo/create-application.html) API with the application metadata
         1. If the application already exists
            1. Get the application id from the 4xx error message
            2. Call SAR [UpdateApplication](https://docs.aws.amazon.com/cli/latest/reference/serverlessrepo/update-application.html) API with the application metadata
            3. Call SAR [CreateApplicationVersion](https://docs.aws.amazon.com/cli/latest/reference/serverlessrepo/create-application-version.html) API with the application metadata if SemanticVersion is specified in the Metadata section of the template
   4. Get the job id from the CodePipeline invoke event
   5. Call CodePipeline [PutJobSuccessResult](https://docs.aws.amazon.com/codepipeline/latest/APIReference/API_PutJobSuccessResult.html) API with job id if succeed. Otherwise, call CodePipeline [PutJobFailureResult](https://docs.aws.amazon.com/codepipeline/latest/APIReference/API_PutJobFailureResult.html) API with job id and failure details from serverlessrepo.publish_application()


## License Summary

This sample code is made available under the MIT license. 
