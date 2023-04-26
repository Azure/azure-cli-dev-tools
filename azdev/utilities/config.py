# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os

from knack.config import CLIConfig
from .const import CHANGE_RULE_MESSAGE_MAPPING, CHANGE_SUGGEST_MESSAGE_MAPPING


def get_azdev_config():
    return CLIConfig(config_dir=get_azdev_config_dir(), config_env_var_prefix='AZDEV')


def get_azure_config():
    return CLIConfig(config_dir=get_azure_config_dir(), config_env_var_prefix='AZURE')


def get_azdev_config_dir():
    """ Returns the user's .azdev directory. """
    from azdev.utilities import get_env_path
    env_name = None
    _, env_name = os.path.splitdrive(get_env_path())
    azdev_dir = os.getenv('AZDEV_CONFIG_DIR', None) or os.path.expanduser(os.path.join('~', '.azdev'))
    if not env_name:
        return azdev_dir
    return os.path.join(azdev_dir, 'env_config') + env_name


def get_azure_config_dir():
    """ Returns the user's Azure directory. """
    return os.getenv('AZURE_CONFIG_DIR', None) or os.path.expanduser(os.path.join('~', '.azure'))


def get_change_rule_template(rule_id="1000"):
    """ Return the rule message template"""
    return CHANGE_RULE_MESSAGE_MAPPING.get(rule_id, "Non applicable")


def get_change_suggest_template(rule_id="1000"):
    """ Return the change suggest message template"""
    return CHANGE_SUGGEST_MESSAGE_MAPPING.get(rule_id, "Non applicable")
