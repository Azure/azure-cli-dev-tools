# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import sys

ACTIVATE_PS = 'Activate.ps1'
AZ_AZDEV_DIR = 'AZDEV_CONFIG_DIR'
AZ_CLOUD = 'AzureCloud'
AZ_CONFIG_DIR = 'AZURE_CONFIG_DIR'
AZ_DEV_SRC = 'dev_sources'
BASH_EXE = '/bin/bash'
BASH_NAME_WIN = 'bash.exe'
BAT_ACTIVATE = 'activate.bat'
CLI_SECTION = 'clipath'
CLOUD_SECTION = 'cloud'
COMMAND_MODULE_PREFIX = 'azure-cli-'
CONFIG_NAME = 'config'
ENV_AZ_CONFIG = '$env:AZURE_CONFIG_DIR'
ENV_AZ_DEV_CONFIG = '$env:AZDEV_CONFIG_DIR'
EXTENSION_PREFIX = 'azext_'
EXT_REPO_NAME = 'azure-cli-extensions'
EXT_SECTION = 'extension'
GITHUB_CLI_REPO_URL = 'https://github.com/azure/azure-cli'
IS_WINDOWS = sys.platform.lower() in ['windows', 'win32']
PIP_E_CMD = 'pip install -e '
PIP_R_CMD = 'pip install -r '
PS1_VENV_SET = '$env:VIRTUAL_ENV'
SCRIPTS = 'Scripts'
SHELL = 'SHELL'
UN_ACTIVATE = 'activate'
UN_BIN = 'bin'
UN_EXPORT = 'export'
VENV_CMD = 'python -m venv --system-site-packages '
VENV_CMD3 = 'python3 -m venv --system-site-packages '
VIRTUAL_ENV = 'VIRTUAL_ENV'

ENV_VAR_TEST_MODULES = 'AZDEV_TEST_TESTS'               # comma-separated list of modules to test
ENV_VAR_VIRTUAL_ENV = ['VIRTUAL_ENV', 'CONDA_PREFIX']   # used by system to identify virtual environment
ENV_VAR_TEST_LIVE = 'AZURE_TEST_RUN_LIVE'               # denotes that tests should be run live instead of played back
