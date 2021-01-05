# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import importlib
import os

from knack.log import get_logger
from knack.util import CLIError,ensure_dir


from azdev.utilities import get_ext_repo_paths, find_files, get_cli_repo_path, get_azure_config
from azdev.operations.extensions import list_extensions

logger = get_logger(__name__)


EXTENSIONS_MOD_PREFIX = 'azext_'


def generate_manual_config(mod_name, output_path=None):
    module, mod_path = _get_module(mod_name)
    output_path = _get_output_path(mod_path, output_path)


def parse_module(module):
    pass


def _get_extension_module_input_name(ext_dir):
    pos_mods = [n for n in os.listdir(ext_dir)
                if n.startswith(EXTENSIONS_MOD_PREFIX) and os.path.isdir(os.path.join(ext_dir, n))]
    if len(pos_mods) != 1:
        raise AssertionError("Expected 1 module to load starting with "
                             "'{}': got {}".format(EXTENSIONS_MOD_PREFIX, pos_mods))
    return pos_mods[0]


def _get_cli_module_input_name(mod_name):
    return 'azure.cli.command_modules.{}'.format(mod_name)


def _get_cli_module_path(mod_name):
    cli_path = get_cli_repo_path()
    return os.path.join(cli_path, 'src', 'azure-cli', 'azure', 'cli', 'command_modules', mod_name)


def _get_module(mod_name):
    extensions = list_extensions()
    for ext in extensions:
        if mod_name.lower() == ext['name'].lower():
            try:
                module = importlib.import_module(_get_extension_module_input_name(ext['path']))
                path = ext['path']
                return module, path
            except ModuleNotFoundError:
                raise CLIError("Please execute command 'azdev extension add {}'".format(mod_name))
    try:
        module = importlib.import_module(_get_cli_module_input_name(mod_name))
        path = _get_cli_module_path(mod_name)
        return module, path
    except ModuleNotFoundError:
        raise CLIError("Cannot Find module {}".format(mod_name))


def _get_output_path(mod_path, output_path=None):
    if output_path is None:
        output_dir = os.path.join(mod_path, 'configuration')
        output_path = os.path.join(output_dir, 'commands.yaml')
    else:
        output_dir = os.path.dirname(output_path)
    ensure_dir(output_dir)
    if os.path.exists(output_path):
        raise CLIError("Configuration file already exists.")
    return output_path

