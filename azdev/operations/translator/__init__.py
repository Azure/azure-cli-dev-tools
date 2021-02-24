# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import importlib
import os
import json
from knack.util import CLIError, ensure_dir

from azdev.operations.extensions import list_extensions
from azdev.utilities import get_cli_repo_path
from azdev.operations.translator.argument import build_argument
from azdev.operations.translator.command import build_command
from azdev.operations.translator.command_group import build_command_group
from azdev.operations.translator.utilities import AZDevTransConfigurationCtx, AZDevTransCtx
from azdev.operations.translator.arg_type import AZDevTransRegisteredArgType
from azdev.operations.translator.module_parser import AZDevTransModuleParser
from azdev.operations.translator.hook import hook_azure_cli_core
EXTENSIONS_MOD_PREFIX = 'azext_'


def generate_commands_config(mod_name,
                             output_path=None,
                             overwrite=False,
                             profile='latest',
                             is_extension=False,
                             compact=False):
    hook_azure_cli_core()
    os.environ['AZURE_GENERATE_COMMAND_CONFIG'] = 'True'
    module, mod_path = _get_module(mod_name, is_extension)
    cli_ctx = AZDevTransCtx(profile)
    parser = AZDevTransModuleParser(cli_ctx=cli_ctx)
    parser.load_module(module)
    root = parser.build_commands_tree()
    ctx = AZDevTransConfigurationCtx(cli_ctx=cli_ctx, module=module)
    commands_config = parser.convert_commands_to_config(root, ctx)
    ctx = AZDevTransConfigurationCtx(cli_ctx=cli_ctx, module=module)
    examples_config = parser.convert_examples_to_config(root, ctx)
    _write_configuration(commands_config, 'commands', mod_path, output_path, profile, overwrite, compact)
    _write_configuration(examples_config, 'examples', mod_path, output_path, profile, overwrite, compact)


def _get_extension_module_input_name(ext_dir):
    pos_mods = [n for n in os.listdir(ext_dir)
                if n.startswith(EXTENSIONS_MOD_PREFIX) and os.path.isdir(os.path.join(ext_dir, n))]
    if len(pos_mods) != 1:
        raise ValueError("Expected 1 module to load starting with '{}': got {}".format(EXTENSIONS_MOD_PREFIX, pos_mods))
    return pos_mods[0]


def _get_cli_module_input_name(mod_name):
    return 'azure.cli.command_modules.{}'.format(mod_name)


def _get_cli_module_path(mod_name):
    cli_path = get_cli_repo_path()
    return os.path.join(cli_path, 'src', 'azure-cli', 'azure', 'cli', 'command_modules', mod_name)


def _get_module(mod_name, is_extension):
    if is_extension:
        extensions = list_extensions()
        for ext in extensions:
            if mod_name.lower() == ext['name'].lower():
                try:
                    module = importlib.import_module(_get_extension_module_input_name(ext['path']))
                    path = ext['path']
                    return module, path
                except ModuleNotFoundError:
                    raise CLIError("Please execute command 'azdev extension add {}'".format(mod_name))
        raise CLIError("Cannot find module {} in extension".format(mod_name))

    try:
        module = importlib.import_module(_get_cli_module_input_name(mod_name))
        path = _get_cli_module_path(mod_name)
        return module, path
    except ModuleNotFoundError:
        raise CLIError("Cannot Find module {}".format(mod_name))


def _write_configuration(data, file_name, mod_path, output_dir, profile, overwrite, compact):
    if output_dir is None:
        output_dir = os.path.join(mod_path, 'configuration')
    output_path = os.path.join(output_dir, profile, file_name)
    ensure_dir(os.path.dirname(output_path))

    if compact:
        json_path = "{}.min.json".format(output_path)
    else:
        json_path = "{}.json".format(output_path)
    if os.path.exists(json_path) and not overwrite:
        raise CLIError("{} file {} already exists.".format(json_path))
    with open(json_path, 'w') as fw:
        json.dump(data, fw,
                  allow_nan=False,
                  indent=None if compact else 2,
                  separators=(',', ':') if compact else None)
    print("Output File Success: {}".format(json_path))


# if __name__ == "__main__":
#     def _get_all_mod_names():
#         cli_path = get_cli_repo_path()
#         command_modules_dir = os.path.join(cli_path, 'src', 'azure-cli', 'azure', 'cli', 'command_modules')
#         my_list = os.listdir(command_modules_dir)
#         print(my_list)
#         mod_names = [mod_name for mod_name in my_list if os.path.isdir(os.path.join(command_modules_dir, mod_name))
#                      and not mod_name.startswith('__')]
#         return mod_names
#
#     mod_names = _get_all_mod_names()
#     values = set()
#     for mod_name in mod_names:
#         if mod_name in ['keyvault', 'batch']:
#             continue
#         print(mod_name)
#         generate_commands_config(mod_name)
