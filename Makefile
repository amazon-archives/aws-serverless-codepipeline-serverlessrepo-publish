SHELL := /bin/sh
PY_VERSION := 3.6

export PYTHONUNBUFFERED := 1

BUILD_DIR := dist

PYTHON := $(shell /usr/bin/which python$(PY_VERSION))

.DEFAULT_GOAL := build

clean:
	rm -rf $(BUILD_DIR)

init:
	$(PYTHON) -m pip install pipenv --user
	pipenv sync --dev

compile-app:
	mkdir -p $(BUILD_DIR)
	pipenv run flake8 app
	pipenv run pydocstyle app

test: compile-app
	pipenv run py.test --cov=app -vv test/unit

build: package test

package: compile-app
	# package dependencies in lib dir
	pipenv lock --requirements > $(BUILD_DIR)/requirements.txt
	pipenv run pip install -t $(BUILD_DIR)/app/lib -r $(BUILD_DIR)/requirements.txt