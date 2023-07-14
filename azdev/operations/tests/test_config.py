# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import requests
import yaml

from knack.log import get_logger
from azdev.utilities.path import get_cli_repo_path
from azdev.operations.constant import (
    ENCODING, GLOBAL_PARAMETERS, GENERIC_UPDATE_PARAMETERS, WAIT_CONDITION_PARAMETERS, OTHER_PARAMETERS,
    RED, ORANGE, GREEN, BLUE, GOLD, RED_PCT, ORANGE_PCT, GREEN_PCT, BLUE_PCT, CLI_OWN_MODULES,
    EXCLUDE_COMMANDS, GLOBAL_EXCLUDE_COMMANDS, EXCLUDE_MODULES, CMD_PATTERN, QUO_PATTERN, END_PATTERN,
    DOCS_END_PATTERN, NOT_END_PATTERN, NUMBER_SIGN_PATTERN)

logger = get_logger(__name__)

try:
    with open(os.path.join(get_cli_repo_path(), 'scripts', 'ci', 'cmdcov.yml'), 'r') as file:
        config = yaml.safe_load(file)
# pylint: disable=broad-exception-caught
except Exception:
    url = "https://raw.githubusercontent.com/Azure/azure-cli/dev/scripts/ci/cmdcov.yml"
    response = requests.get(url)
    config = yaml.safe_load(response.text)
print(config)
assert config['ENCODING'] == ENCODING
assert config['GLOBAL_PARAMETERS'] == GLOBAL_PARAMETERS
assert config['GENERIC_UPDATE_PARAMETERS'] == GENERIC_UPDATE_PARAMETERS
assert config['WAIT_CONDITION_PARAMETERS'] == WAIT_CONDITION_PARAMETERS
assert config['OTHER_PARAMETERS'] == OTHER_PARAMETERS
assert config['RED'] == RED
assert config['ORANGE'] == ORANGE
assert config['GREEN'] == GREEN
assert config['BLUE'] == BLUE
assert config['GOLD'] == GOLD
assert config['RED_PCT'] == RED_PCT
assert config['ORANGE_PCT'] == ORANGE_PCT
assert config['GREEN_PCT'] == GREEN_PCT
assert config['BLUE_PCT'] == BLUE_PCT
assert config['CLI_OWN_MODULES'] == CLI_OWN_MODULES
assert config['EXCLUDE_COMMANDS'] == EXCLUDE_COMMANDS
assert config['GLOBAL_EXCLUDE_COMMANDS'] == GLOBAL_EXCLUDE_COMMANDS
assert config['EXCLUDE_MODULES'] == EXCLUDE_MODULES
assert config['CMD_PATTERN'] == CMD_PATTERN
assert config['QUO_PATTERN'] == QUO_PATTERN
assert config['END_PATTERN'] == END_PATTERN
assert config['DOCS_END_PATTERN'] == DOCS_END_PATTERN
assert config['NOT_END_PATTERN'] == NOT_END_PATTERN
assert config['NUMBER_SIGN_PATTERN'] == NUMBER_SIGN_PATTERN
