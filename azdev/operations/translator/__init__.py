# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import importlib
import os

from knack.cli import CLI
from knack.commands import CLICommandsLoader
from knack.log import get_logger
from knack.util import CLIError, ensure_dir

from azdev.operations.extensions import list_extensions
from azdev.utilities import get_cli_repo_path

logger = get_logger(__name__)

EXTENSIONS_MOD_PREFIX = 'azext_'


class AZDevTranslatorCtx(CLI):

    def __init__(self, **kwargs):
        super(AZDevTranslatorCtx, self).__init__(**kwargs)
        self.data['headers'] = {}
        self.data['command'] = 'unknown'
        self.data['command_extension_name'] = None
        self.data['completer_active'] = False
        self.data['query_active'] = False


class AZDevTranslatorModuleParser(CLICommandsLoader):

    def __init__(self, cli_ctx=None, **kwargs):
        cli_ctx = cli_ctx or AZDevTranslatorCtx()
        super(AZDevTranslatorModuleParser, self).__init__(cli_ctx=cli_ctx, **kwargs)
        self.cmd_to_loader_map = {}

    def load_module(self, module):
        command_table, command_group_table = self._load_module_command_loader(module)
        for cmd in command_table.values():
            cmd.command_source = module
        self.command_table.update(command_table)
        self.command_group_table.update(command_group_table)

    def _load_module_command_loader(self, module):
        loader_cls = getattr(module, 'COMMAND_LOADER_CLS', None)
        if not loader_cls:
            raise CLIError("Module is missing `COMMAND_LOADER_CLS` entry.")
        command_loader = loader_cls(cli_ctx=self.cli_ctx)
        command_table = command_loader.load_command_table(None)
        if command_table:
            for cmd in list(command_table.keys()):
                self.cmd_to_loader_map[cmd] = [command_loader]

        return command_table, command_loader.command_group_table

    def build_commands_tree(self):
        pass


def generate_manual_config(mod_name, output_path=None, overwrite=False):
    module, mod_path = _get_module(mod_name)
    output_path = _get_output_path(mod_path, output_path, overwrite)
    parser = AZDevTranslatorModuleParser()
    parser.load_module(module)


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


def _get_output_path(mod_path, output_path, overwrite):
    if output_path is None:
        output_dir = os.path.join(mod_path, 'configuration')
        output_path = os.path.join(output_dir, 'commands.yaml')
    else:
        output_dir = os.path.dirname(output_path)
    ensure_dir(output_dir)
    if os.path.exists(output_path) and not overwrite:
        raise CLIError("Configuration file already exists.")
    return output_path
