## AWS CodePipeline SAR Auto-Publish ![Build Status](https://codebuild.us-east-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoiRWVJS0x2ZFJGMTJYZWVKWHRxZXQzV3dHYlM4enJPc3k3bno4cmZRMmtwQkR5dGRSYUp1bDF3bnNHUE1NV1JpTHpTWC9KZ1Q4YmhtcG5aOXdNVWd4U2ZBPSIsIml2UGFyYW1ldGVyU3BlYyI6IlVhNGJ2dXlnZG1kbHJLS2siLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=master)

This is a serverless app that provides automated publishing of serverless applications to the AWS Serverless Application Repository (SAR) via AWS CodePipeline. See [this tutorial](https://docs.aws.amazon.com/codepipeline/latest/userguide/tutorials-serverlessrepo-auto-publish.html) for a step-by-step walkthrough.

## Architecture

![App Architecture](https://github.com/awslabs/aws-serverless-codepipeline-serverlessrepo-publish/raw/master/images/app-architecture.png)

This app contains a single Lambda function: ServerlessRepoPublish. It uses convenience helpers from the [serverlessrepo](https://pypi.org/project/serverlessrepo/) python module to publish applications to SAR.

1. A code change is made to a serverless application and pushed to the source repository, which is the source provider of the CodePipeline pipeline.
2. The code change flows through the pipeline and outputs a packaged SAM template as a stage output.
3. ServerlessRepoPublish lambda is invoked by CodePipeline as part of the Invoke Action of the pipeline.
4. ServerlessRepoPublish lambda gets the packaged SAM template from CodePipeline artifact store S3 bucket.
5. ServerlessRepoPublish lambda calls serverlessrepo.publish_application() with the packaged template as input. It will perform either create or update logic for the serverless application. See [here](https://pypi.org/project/serverlessrepo/) for details on the python module behavior.
6. ServerlessRepoPublish lambda calls CodePipeline [PutJobSuccessResult](https://docs.aws.amazon.com/codepipeline/latest/APIReference/API_PutJobSuccessResult.html) API with job id if publish is successful. Otherwise, call CodePipeline [PutJobFailureResult](https://docs.aws.amazon.com/codepipeline/latest/APIReference/API_PutJobFailureResult.html) API with job id and failure details from serverlessrepo.publish_application()

## Installation Instructions

For a step-by-step walkthrough of using this app with AWS CodePipeline, see [this tutorial](https://docs.aws.amazon.com/codepipeline/latest/userguide/tutorials-serverlessrepo-auto-publish.html).

You can also embed this app in the same SAM template that defines your CodePipeline and artifact store bucket using [nested apps](https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md#awsserverlessapplication). Below is a SAM template snippet that nests AWS CodePipeline SAR Auto-Publish app and creates a three-stage (Source, Build, Deploy) pipeline:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: 'AWS::Serverless-2016-10-31'

Resources:
  CodePipelineServerlessRepoPublishApp:
    Type: 'AWS::Serverless::Application'
    Properties:
      Location:
        ApplicationId: 'arn:aws:serverlessrepo:us-east-1:077246666028:applications/aws-serverless-codepipeline-serverlessrepo-publish'
        SemanticVersion: 1.0.0

  Pipeline:
    Type: AWS::CodePipeline::Pipeline
    Properties:
      ArtifactStore:
        Type: S3
        Location:
          Ref: ArtifactStoreBucket
      RoleArn: !GetAtt PipelineRole.Arn
      Stages:
        - Name: Source
          Actions:
            - Name: Source
              ActionTypeId:
                Category: Source
                Owner: AWS
                Provider: S3
                Version: '1'
              Configuration:
                S3Bucket: <YourSourceBucket>
                S3ObjectKey: <YourSourceKey>
              OutputArtifacts:
                - Name: SourceArtifact
              RunOrder: '1'
        - Name: Build
          Actions:
            - Name: Build
              ActionTypeId:
                Category: Build
                Owner: AWS
                Provider: CodeBuild
                Version: '1'
              Configuration:
                ProjectName: <YourCodeBuildProjectName>
              InputArtifacts:
                - Name: SourceArtifact
              OutputArtifacts:
                - Name: BuildArtifact
              RunOrder: '1'
        - Name: Deploy
          Actions:
            - Name: DeployToServerlessRepo
              ActionTypeId:
                Category: Invoke
                Owner: AWS
                Provider: Lambda
                Version: '1'
              Configuration:
                FunctionName: !GetAtt CodePipelineServerlessRepoPublishApp.Outputs.ServerlessRepoPublishFunctionName # Here we use the app output ServerlessRepoPublishFunctionName
              InputArtifacts:
                - Name: BuildArtifact
              RunOrder: '1'

  PipelineRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Statement:
        - Action: ['sts:AssumeRole']
          Effect: Allow
          Principal:
            Service: [codepipeline.amazonaws.com]
        Version: '2012-10-17'
      Path: /
      Policies:
        - PolicyName: CodePipelineAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
            - Action:
              - 'iam:PassRole'
              Effect: Allow
              Resource: '*'
            - Effect: Allow
              Action:
              - "codebuild:BatchGetBuilds"
              - "codebuild:StartBuild"
              Resource:
              - <YourCodeBuildProjectArn>
            - Effect: Allow
              Action:
              - "lambda:InvokeFunction"
              Resource:
              - !GetAtt CodePipelineServerlessRepoPublishApp.Outputs.ServerlessRepoPublishFunctionArn # Here we use the app output ServerlessRepoPublishFunctionArn
            - Action:
              - 's3:ListBucket'
              - 's3:GetBucketVersioning'
              Effect: Allow
              Resource:
              - !Sub ${ArtifactStoreBucket.Arn}
              - <YourSourceBucketArn>
            - Action:
              - 's3:PutObject'
              - 's3:GetObject'
              - 's3:GetObjectVersion'
              Effect: Allow
              Resource:
              - !Sub ${ArtifactStoreBucket.Arn}/*
              - <YourSourceBucketArn>

  ArtifactStoreBucket:
    Type: AWS::S3::Bucket
    Properties:
      VersioningConfiguration:
        Status: Enabled
```

## App Parameters

1. `LogLevel` (optional) - Log level for Lambda function logging, e.g., ERROR, INFO, DEBUG, etc. Default: INFO

## App Outputs

1. `ServerlessRepoPublishFunctionName` - ServerlessRepoPublish lambda function name.
1. `ServerlessRepoPublishFunctionArn` - ServerlessRepoPublish lambda function ARN.

## License Summary

This code is made available under the MIT license. See the LICENSE file.
