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

ENV_VAR_TEST_MODULES = 'AZDEV_TEST_TESTS'               # comma-separated list of modules to test
ENV_VAR_VIRTUAL_ENV = ['VIRTUAL_ENV', 'CONDA_PREFIX']   # used by system to identify virtual environment
ENV_VAR_TEST_LIVE = 'AZURE_TEST_RUN_LIVE'               # denotes that tests should be run live instead of played back

BREAKING_CHANE_RULE_LINK_URL_PREFIX = "https://github.com/Azure/azure-cli/blob/dev/doc/breaking_change_rules/"
BREAKING_CHANE_RULE_LINK_URL_SUFFIX = ".md"

CMD_PROPERTY_REMOVE_BREAK_LIST = []
CMD_PROPERTY_ADD_BREAK_LIST = ["confirmation"]
CMD_PROPERTY_UPDATE_BREAK_LIST = []
CMD_PROPERTY_IGNORED_LIST = ["is_aaz", "supports_no_wait"]

PARA_PROPERTY_REMOVE_BREAK_LIST = ["options", "id_part", "nargs"]
PARA_PROPERTY_ADD_BREAK_LIST = ["required", "choices", "type"]
PARA_PROPERTY_UPDATE_BREAK_LIST = ["default", "aaz_default", "type"]
PARA_NAME_IGNORED_LIST = ["force_string"]
PARA_PROPERTY_IGNORED_LIST = []
PARA_VALUE_IGNORED_LIST = ["generic_update_set", "generic_update_add", "generic_update_remove",
                           "generic_update_force_string"]

CHANGE_RULE_MESSAGE_MAPPING = {
    "1000": "default Message",
    "1001": "cmd `{0}` added",
    "1002": "cmd `{0}` removed",
    "1003": "cmd `{0}` added property `{1}`",
    "1004": "cmd `{0}` removed property `{1}`",
    "1005": "cmd `{0}` updated property `{1}` from `{2}` to `{3}`",
    "1006": "cmd `{0}` added parameter `{1}`",
    "1007": "cmd `{0}` removed parameter `{1}`",
    "1008": "cmd `{0}` update parameter `{1}`: added property `{2}`",
    "1009": "cmd `{0}` update parameter `{1}`: removed property `{2}`",
    "1010": "cmd `{0}` update parameter `{1}`: updated property `{2}` from `{3}` to `{4}`",
    "1011": "sub group `{0}` added",
    "1012": "sub group `{0}` removed",
}

CHANGE_SUGGEST_MESSAGE_MAPPING = {
    "1000": "default Message",
    "1001": "please confirm cmd `{0}` added",
    "1002": "please confirm cmd `{0}` removed",
    "1003": "please remove property `{0}` for cmd `{1}`",
    "1004": "please add back property `{0}` for cmd `{1}`",
    "1005": "please change property `{0}` from `{1}` to `{2}` for cmd `{3}`",
    "1006": "please remove parameter `{0}` for cmd `{1}`",
    "1007": "please add back parameter `{0}` for cmd `{1}`",
    "1008": "please remove property `{0}` for parameter `{1}` for cmd `{2}`",
    "1009": "please add back property `{0}` for parameter {1}` for cmd `{2}`",
    "1010": "please change property `{0}` from `{1}` to `{2}` for parameter `{3}` of cmd `{4}`",
    "1011": "please confirm sub group `{0}` added",
    "1012": "please confirm sub group `{0}` removed",
}
