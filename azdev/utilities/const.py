# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import sys

COMMAND_MODULE_PREFIX = 'azure-cli-'
EXTENSION_PREFIX = 'azext_'
EXT_REPO_NAME = 'azure-cli-extensions'
IS_WINDOWS = sys.platform.lower() in ['windows', 'win32']
CONFIG_NAME = 'config'
ACTIVATE_PS = 'Activate.ps1'
PS1_VENV_SET = '$env:VIRTUAL_ENV'
SCRIPTS = 'Scripts'
VIRTUAL_ENV = 'VIRTUAL_ENV'
VENV_CMD = 'python -m venv --system-site-packages '
VENV_CMD3 = 'python3 -m venv --system-site-packages '
AZ_CONFIG_DIR = 'AZURE_CONFIG_DIR'
AZ_AZDEV_DIR = 'AZDEV_CONFIG_DIR'
AZ_DEV_SRC = 'dev_sources'
AZ_CLOUD = 'AzureCloud'
CLOUD_SECTION = 'cloud'
EXT_SECTION = 'extension'
CLI_SECTION = 'clipath'
REST_SPEC_SECTION = 'restspec'
EVN_AZ_CONFIG = '$env:AZURE_CONFIG_DIR'
EVN_AZ_DEV_CONFIG = '$env:AZDEV_CONFIG_DIR'
AZEX_PREFIX = 'azext_'
INSTALL_EXT_CMD = 'pip install -e .'
PIP_E_CMD = 'pip install -e '
AUTO_REST_CMD = 'autorest --az --azure-cli-extension-folder='
UN_BIN = 'bin'
UN_ACTIVATE = 'activate'
UN_EXPORT = 'export'
BAT_ACTIVATE = 'activate.bat'
BASH_EXE = '/bin/bash'
GIT_CLONE_CMD = 'git clone --no-checkout '
GIT_SPARSE_CHECKOUT_CMD = 'git sparse-checkout set '
GIT_SWAGGER_REPO_URL = 'https://github.com/Azure/azure-rest-api-specs.git'
SWAGGER_REPO_NAME = 'azure-rest-api-specs'

ENV_VAR_TEST_MODULES = 'AZDEV_TEST_TESTS'               # comma-separated list of modules to test
ENV_VAR_VIRTUAL_ENV = ['VIRTUAL_ENV', 'CONDA_PREFIX']   # used by system to identify virtual environment
ENV_VAR_TEST_LIVE = 'AZURE_TEST_RUN_LIVE'               # denotes that tests should be run live instead of played back
