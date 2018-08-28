SHELL := /bin/sh
PY_VERSION := 3.6

export PYTHONUNBUFFERED := 1

BUILD_DIR := dist
TEMPLATE_DIR := sam

# Required environment variables (user must override)

# S3 bucket used for packaging SAM templates
PACKAGE_BUCKET ?= <bucket>

# user can optionally override the following by setting environment variables with the same names before running make

# Stack name used when deploying the app for manual testing
APP_STACK_NAME ?= aws-serverless-codepipeline-serverlessrepo-publish
# GitHub owner.
GITHUB_OWNER ?= awslabs
# GitHub repo.
GITHUB_REPO ?= aws-serverless-codepipeline-serverlessrepo-publish
# Stack name used when deploying the app for manual testing
# Name of stack that creates the CI/CD pipeline for testing and publishing this app
CICD_STACK_NAME ?= cicd-aws-serverless-codepipeline-serverlessrepo-publish

PYTHON := $(shell /usr/bin/which python$(PY_VERSION))

.DEFAULT_GOAL := build

clean:
	rm -rf $(BUILD_DIR)

init:
	$(PYTHON) -m pip install pipenv --user
	pipenv sync --dev

init-cicd:
	pipenv run sam deploy --template-file $(TEMPLATE_DIR)/cicd.yml --stack-name $(CICD_STACK_NAME) --parameter-overrides GitHubOwner="$(GITHUB_OWNER)" GitHubRepo="$(GITHUB_REPO)" --capabilities CAPABILITY_IAM

compile-app:
	mkdir -p $(BUILD_DIR)
	pipenv run flake8 app
	pipenv run pydocstyle app

test: compile-app
	pipenv run py.test --cov=app -vv test/unit

build: package test

package: compile-app
	cp -r $(TEMPLATE_DIR)/app.yml app $(BUILD_DIR)

	# package dependencies in lib dir
	pipenv lock --requirements > $(BUILD_DIR)/requirements.txt
	pipenv run pip install -t $(BUILD_DIR)/app/lib -r $(BUILD_DIR)/requirements.txt

deploy: package
	pipenv run sam package --template-file $(BUILD_DIR)/app.yml --s3-bucket $(PACKAGE_BUCKET) --output-template-file $(BUILD_DIR)/packaged-app.yml
	pipenv run sam deploy --template-file $(BUILD_DIR)/packaged-app.yml --stack-name $(APP_STACK_NAME) --capabilities CAPABILITY_IAM