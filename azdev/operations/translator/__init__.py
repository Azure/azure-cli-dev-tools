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
from knack.deprecation import Deprecated

from azdev.operations.extensions import list_extensions
from azdev.utilities import get_cli_repo_path

logger = get_logger(__name__)

EXTENSIONS_MOD_PREFIX = 'azext_'


class AZDevTransCtx(CLI):

    def __init__(self, **kwargs):
        super(AZDevTransCtx, self).__init__(**kwargs)
        self.data['headers'] = {}
        self.data['command'] = 'unknown'
        self.data['command_extension_name'] = None
        self.data['completer_active'] = False
        self.data['query_active'] = False


class AZDevTransDeprecateInfo:

    _PLACEHOLDER_INSTANCE = Deprecated(
        redirect='{redirect}',  # use {redirect} as placeholder value in template
        hide='{hide}',
        expiration='{expiration}',
        object_type='{object_type}',
        target='{target}'
    )

    _DEFAULT_TAG_TEMPLATE = _PLACEHOLDER_INSTANCE._get_tag(_PLACEHOLDER_INSTANCE)
    _DEFAULT_MESSAGE_TEMPLATE = _PLACEHOLDER_INSTANCE._get_message(_PLACEHOLDER_INSTANCE)

    def __init__(self, table_instance):
        self.redirect = table_instance.redirect
        self.hide = table_instance.hide
        self.expiration = table_instance.expiration
        self.tag_template = table_instance._get_tag(self._PLACEHOLDER_INSTANCE)
        self.message_template = table_instance._get_message(self._PLACEHOLDER_INSTANCE)


class AZDevTransCommandGroup:

    def __init__(self, name, parent_group, full_name, table_instance):
        self.name = name
        self.parent_group = parent_group
        self.full_name = full_name

        self.sub_groups = {}
        self.sub_commands = {}

        self.deprecate_info = None
        self.is_preview = None
        self.is_experimental = None
        if not table_instance:
            return

        if 'deprecate_info' in table_instance.group_kwargs:
            self.deprecate_info = AZDevTransDeprecateInfo(table_instance.group_kwargs['deprecate_info'])

        if 'preview_info' in table_instance.group_kwargs:
            self.is_preview = True

        if 'experimental_info' in table_instance.group_kwargs:
            self.is_experimental = True


class AZDevTransCommand:

    def __init__(self, name, parent_group, full_name, table_instance):
        self.name = name
        self.parent_group = parent_group
        self.full_name = full_name

        self.sub_arguments = {}

        self.deprecate_info = None
        self.is_preview = None
        self.is_experimental = None

        if table_instance.deprecate_info:
            self.deprecate_info = AZDevTransDeprecateInfo(table_instance.deprecate_info)

        if table_instance.preview_info:
            self.is_preview = True

        if table_instance.experimental_info:
            self.is_experimental = True


class AZDevTransArgument:

    def __init__(self, name, parent_command,
                 options_list=None, id_part=None, completer=None, validator=None, configured_default=None,
                 arg_group=None, arg_type=None, deprecate_info=None,
                 option_strings=None, dest=None,
                 nargs=None, const=None, default=None, type=None, choices=None, required=None, help=None, metavar=None,
                 action=None, default_value_source=None,
                 min_api=None, max_api=None, resource_type=None, operation_group=None, custom_command_type=None,
                 command_type=None, is_preview=None, preview_info=None, is_experimental=None, experimental_info=None,
                 local_context_attribute=None):
        self.name = name
        self.parent_command = parent_command


class AZDevTransModuleParser(CLICommandsLoader):

    def __init__(self, cli_ctx=None, **kwargs):
        cli_ctx = cli_ctx or AZDevTransCtx()
        super(AZDevTransModuleParser, self).__init__(cli_ctx=cli_ctx, **kwargs)
        self.cmd_to_loader_map = {}

    def load_module(self, module):
        command_table, command_group_table = self._load_module_command_loader(module)
        for command in command_table.values():
            command.command_source = module
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
        root = AZDevTransCommandGroup(name='az', full_name='', parent_group=None, table_instance=None)
        self._add_sub_command_groups(parent_group=root, prefix='')
        self._add_sub_commands(parent_group=root, prefix='')
        return root

    def _add_sub_command_groups(self, parent_group, prefix):
        for full_name in self.command_group_table:
            key_words = full_name.split()
            if len(key_words) == 0:
                continue

            if prefix == ' '.join(key_words[:-1]):
                name = key_words[-1]
                group = AZDevTransCommandGroup(
                    name=name, parent_group=parent_group, full_name=full_name,
                    table_instance=self.command_group_table[full_name]
                )
                parent_group.sub_groups[name] = group
                sub_prefix = '{} {}'.format(prefix, name).strip()
                self._add_sub_command_groups(parent_group=group, prefix=sub_prefix)
                self._add_sub_commands(parent_group=group, prefix=sub_prefix)

    def _add_sub_commands(self, parent_group, prefix):
        for full_name in self.command_table:
            key_words = full_name.split()
            if prefix == ' '.join(key_words[:-1]):
                name = key_words[-1]
                command = AZDevTransCommand(
                    name=name, parent_group=parent_group, full_name=full_name,
                    table_instance=self.command_table[full_name]
                )
                parent_group.sub_commands[name] = command
                self._add_sub_arguments(command=command)

    def _add_sub_arguments(self, command):
        pass


def generate_manual_config(mod_name, output_path=None, overwrite=False):
    module, mod_path = _get_module(mod_name)
    parser = AZDevTransModuleParser()
    parser.load_module(module)
    parser.build_commands_tree()

    # output_path = _get_output_path(mod_path, output_path, overwrite)


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
