SHELL := /bin/sh
PY_VERSION := 3.7

export PYTHONUNBUFFERED := 1

SRC_DIR := src
TEST_DIR := test
SAM_DIR := .aws-sam
TEMPLATE_DIR := sam

# Required environment variables (user must override)

# S3 bucket used for packaging SAM templates
PACKAGE_BUCKET ?= aws-sar-publishing
INTEG_TEST_BUCKET ?= codepipeline-sar-publish-integ-tests


# user can optionally override the following by setting environment variables with the same names before running make

# Path to system pip
PIP ?= pip
# Default AWS CLI region
AWS_DEFAULT_REGION ?= us-east-1

# Stack name used when deploying the app for manual testing
APP_STACK_NAME ?= aws-serverless-codepipeline-serverlessrepo-publish
# GitHub owner.
GITHUB_OWNER ?= awslabs
# GitHub repo.
GITHUB_REPO ?= aws-serverless-codepipeline-serverlessrepo-publish
# Stack name used when deploying the app for manual testing
# Name of stack that creates the CI/CD pipeline for testing and publishing this app
CICD_STACK_NAME ?= cicd-$(GITHUB_REPO)

PYTHON := $(shell /usr/bin/which python$(PY_VERSION))

.DEFAULT_GOAL := build

clean:
	rm -f $(SRC_DIR)/requirements.txt
	rm -rf $(SAM_DIR)

# used by CI build to install dependencies
init:
	$(PYTHON) -m pip install pipenv --user
	pipenv sync --dev

init-cicd:
	pipenv run sam deploy --template-file $(TEMPLATE_DIR)/cicd.yml --stack-name $(CICD_STACK_NAME) --parameter-overrides GitHubOwner="$(GITHUB_OWNER)" GitHubRepo="$(GITHUB_REPO)" --capabilities CAPABILITY_IAM

compile:
	pipenv run flake8 $(SRC_DIR) $(TEST_DIR)
	pipenv run pydocstyle $(SRC_DIR)
	pipenv run cfn-lint $(TEMPLATE_DIR)/app.yml
	pipenv run py.test --cov=$(SRC_DIR) --cov-fail-under=85 -vv test/unit
	pipenv lock --requirements > $(SRC_DIR)/requirements.txt
	pipenv run sam build -t $(TEMPLATE_DIR)/app.yml -m $(SRC_DIR)/requirements.txt --debug

integ-test: compile
	sam package --template-file $(SAM_DIR)/build/template.yaml --s3-bucket $(INTEG_TEST_BUCKET) --output-template-file $(SAM_DIR)/packaged-app.yml
	aws s3api put-object --bucket $(INTEG_TEST_BUCKET) --key template.yml --body $(SAM_DIR)/packaged-app.yml
	aws s3api put-object --bucket $(INTEG_TEST_BUCKET) --key test_environment.yml --body $(TEST_DIR)/integration/test_environment.yml
	pipenv run py.test --cov=$(SRC_DIR) -s -vv test/integration

build: compile

package: compile
	pipenv run sam package --template-file $(SAM_DIR)/build/template.yaml --s3-bucket $(PACKAGE_BUCKET) --output-template-file $(SAM_DIR)/packaged-app.yml

publish: package
	pipenv run sam publish --template $(SAM_DIR)/packaged-app.yml

deploy: package
	pipenv run sam package --template-file $(SAM_DIR)/app.yml --s3-bucket $(PACKAGE_BUCKET) --output-template-file $(SAM_DIR)/packaged-app.yml
	pipenv run sam deploy --template-file $(SAM_DIR)/packaged-app.yml --stack-name $(APP_STACK_NAME) --capabilities CAPABILITY_IAM
