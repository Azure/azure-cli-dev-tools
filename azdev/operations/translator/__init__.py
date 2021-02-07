# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import importlib
import os
from collections import defaultdict, OrderedDict
import json

from knack.cli import CLI
from knack.commands import CLICommandsLoader
from knack.log import get_logger
from knack.util import CLIError, ensure_dir
from knack.arguments import ArgumentRegistry

from azdev.operations.extensions import list_extensions
from azdev.utilities import get_cli_repo_path
from azdev.operations.translator.argument import build_argument
from azdev.operations.translator.command import build_command
from azdev.operations.translator.command_group import build_command_group
from azdev.operations.translator.utilities import ConfigurationCtx
from azdev.operations.translator.arg_type import AZDevTransArgTypeInstance
import datetime

logger = get_logger(__name__)

EXTENSIONS_MOD_PREFIX = 'azext_'


class AZDevTransInvocation(object):

    def __init__(self, *args, **kwargs):
        self.data = defaultdict(lambda: None)


class AZDevTransCtx(CLI):

    def __init__(self, profile, **kwargs):
        from azure.cli.core.cloud import get_active_cloud
        from azure.cli.core.profiles import API_PROFILES
        super(AZDevTransCtx, self).__init__(**kwargs)
        self.data['headers'] = {}
        self.data['command'] = 'unknown'
        self.data['command_extension_name'] = None
        self.data['completer_active'] = False
        self.data['query_active'] = False

        if profile not in API_PROFILES:
            raise CLIError('Invalid --profile value "{}"'.format(profile))
        self.cloud = get_active_cloud(self)
        self.cloud.profile = profile
        self.invocation = AZDevTransInvocation()

    def get_cli_version(self):
        from azure.cli.core import __version__
        return __version__

    def _should_enable_color(self):
        return False


class AZDevTransModuleParser(CLICommandsLoader):

    def __init__(self, cli_ctx=None, profile=None, **kwargs):
        cli_ctx = cli_ctx or AZDevTransCtx(profile)
        super(AZDevTransModuleParser, self).__init__(cli_ctx=cli_ctx, **kwargs)
        self.cmd_to_loader_map = {}

    def load_module(self, module):
        command_table, command_group_table, command_loader = self._load_module_command_loader(module)
        for command in command_table.values():
            command.command_source = module
        self.command_table.update(command_table)
        self.command_group_table.update(command_group_table)
        self.command_loader_registry_argument(command_loader)

    @staticmethod
    def get_argument_context_cls(parent_cls):

        class AZDevArgumentContext(parent_cls):
            def __init__(self, *args, **kwargs):
                super(AZDevArgumentContext, self).__init__(*args, **kwargs)

            def _handle_experimentals(self, argument_dest, **kwargs):
                return kwargs

            def _handle_previews(self, argument_dest, **kwargs):
                return kwargs

            def _handle_deprecations(self, argument_dest, **kwargs):
                return kwargs.get('action', None)

        return AZDevArgumentContext

    def command_loader_registry_argument(self, command_loader):
        command_loader.supported_api_version = lambda **kwargs: True
        command_loader.skip_applicability = True
        command_loader._argument_context_cls = self.get_argument_context_cls(command_loader._argument_context_cls)
        command_loader.argument_registry = ArgumentRegistry()
        command_loader.extra_argument_registry = defaultdict(lambda: {})
        command_loader.load_arguments(None)

    def _load_module_command_loader(self, module):
        loader_cls = getattr(module, 'COMMAND_LOADER_CLS', None)
        if not loader_cls:
            if hasattr(module, 'get_command_loader'):
                loader_cls = module.get_command_loader(self.cli_ctx)
            else:
                raise CLIError("Module is missing `COMMAND_LOADER_CLS` entry.")
        command_loader = loader_cls(cli_ctx=self.cli_ctx)
        command_table = command_loader.load_command_table(None)
        if command_table:
            for cmd in list(command_table.keys()):
                self.cmd_to_loader_map[cmd] = [command_loader]

        return command_table, command_loader.command_group_table, command_loader

    def build_commands_tree(self):
        root = build_command_group(name='az', full_name='', parent_group=None, table_instance=None)
        self._add_sub_command_groups(parent_group=root, prefix='')
        self._add_sub_commands(parent_group=root, prefix='')
        return root

    def convert_commands_to_config(self, root, ctx):
        config = OrderedDict()
        config['created'] = str(datetime.datetime.now())
        if ctx.imports:
            config['imports'] = ctx.imports
        k, v = root.to_config(ctx)
        config[k] = v
        return config

    def convert_examples_to_config(self, root, ctx):
        k, v = root.to_example_config(ctx)
        config = OrderedDict()
        config['created'] = str(datetime.datetime.now())
        config[k] = v
        return config

    def _add_sub_command_groups(self, parent_group, prefix):
        for full_name in self.command_group_table:
            key_words = full_name.split()
            if len(key_words) == 0:
                continue

            if prefix == ' '.join(key_words[:-1]):
                name = key_words[-1]
                group = build_command_group(
                    name=name, parent_group=parent_group, full_name=full_name,
                    table_instance=self.command_group_table[full_name]
                )
                parent_group.sub_groups[name] = group
                sub_prefix = '{} {}'.format(prefix, name).strip()
                self._add_sub_command_groups(parent_group=group, prefix=sub_prefix)
                self._add_sub_commands(parent_group=group, prefix=sub_prefix)

        registered_arg_types = parent_group.registered_arg_types
        for sub_command_name, sub_command_group in parent_group.sub_groups.items():
            for register_name, arg_types in sub_command_group.registered_arg_types.items():
                if register_name not in registered_arg_types:
                    registered_arg_types[register_name] = {}
                arg_type = [*arg_types.values()][0]
                registered_arg_types[register_name][sub_command_name] = arg_type

    def _add_sub_commands(self, parent_group, prefix):
        for full_name in self.command_table:
            key_words = full_name.split()
            if prefix == ' '.join(key_words[:-1]):
                name = key_words[-1]
                table_instance = self.command_table[full_name]
                command = build_command(
                    name=name, parent_group=parent_group, full_name=full_name,
                    table_instance=table_instance
                )
                self._add_sub_arguments(command=command, table_instance=table_instance)
                parent_group.sub_commands[name] = command

        registered_arg_types = parent_group.registered_arg_types
        for sub_command_name, sub_command in parent_group.sub_commands.items():
            for register_name, arg_types in sub_command.registered_arg_types.items():
                if register_name not in registered_arg_types:
                    registered_arg_types[register_name] = {}
                arg_type = [*arg_types.values()][0]
                registered_arg_types[register_name][sub_command_name] = arg_type

    def _add_sub_arguments(self, command, table_instance):

        loader = table_instance.loader
        assert table_instance.arguments_loader, 'Command "{}" does not have arguments loader'.format(command.full_name)

        command_args = dict(table_instance.arguments_loader())

        arg_registry = loader.argument_registry
        extra_arg_registry = loader.extra_argument_registry
        for arg_name, definition in extra_arg_registry[command.full_name].items():
            command_args[arg_name] = definition
        for arg_name, arg in command_args.items():
            overrides = arg_registry.get_cli_argument(command.full_name, arg_name)
            arg.type.update(other=overrides)

        for arg_name, arg in command_args.items():
            if arg_name in ['cmd', 'properties_to_set', 'properties_to_add', 'properties_to_remove', 'force_string', 'no_wait', '_cache']:
                continue
            command.sub_arguments[arg_name] = build_argument(arg_name, parent_command=command, table_instance=arg)

        registered_arg_types = command.registered_arg_types
        for arg_name, arg in command.sub_arguments.items():
            if arg.arg_type is not None and isinstance(arg.arg_type, AZDevTransArgTypeInstance):
                arg_type = arg.arg_type
                if arg_type.register_name not in registered_arg_types:
                    registered_arg_types[arg_type.register_name] = {}
                registered_arg_types[arg_type.register_name][arg_name] = arg_type


def generate_commands_config(mod_name,
                             output_path=None,
                             overwrite=False,
                             profile='latest',
                             is_extension=False,
                             compact=False):
    module, mod_path = _get_module(mod_name, is_extension)
    parser = AZDevTransModuleParser(profile=profile)
    parser.load_module(module)
    root = parser.build_commands_tree()
    imports = {
        'get_three_state_action': 'azure.cli.core.commands.parameters#get_three_state_action',
        'get_three_state_flag': 'azure.cli.core.commands.parameters#get_three_state_flag',
        'get_enum_type': 'azure.cli.core.commands.parameters#get_enum_type',
        'EnumAction': 'azure.cli.core.commands.parameters#EnumAction',
        'FilesCompleter': 'azure.cli.core.translator.completer#FilesCompleter',
        'file_type': 'azure.cli.core.commands.parameters#file_type',
        'get_location_type': 'azure.cli.core.commands.parameters#get_location_type',
        'get_resource_name_completion_list': 'azure.cli.core.commands.parameters#get_resource_name_completion_list',
        'get_default_location_from_resource_group': 'azure.cli.core.commands.validators#get_default_location_from_resource_group',
        'get_location_completion_list': 'azure.cli.core.commands.parameters#get_location_completion_list',
        'get_location_name_type': 'azure.cli.core.commands.parameters#get_location_name_type',
        'deployment_validate_table_format': 'azure.cli.core.commands.arm#deployment_validate_table_format',
        'handle_template_based_exception': 'azure.cli.core.commands.arm#handle_template_based_exception',
        'json_object_type': 'azure.cli.core.commands.parameters#json_object_type',
        'get_resource_group_completion_list': 'azure.cli.core.commands.parameters#get_resource_group_completion_list',
        'validate_tags': 'azure.cli.core.commands.validators#validate_tags'
    }
    ctx = ConfigurationCtx(module=module, imports=imports)
    commands_config = parser.convert_commands_to_config(root, ctx)
    ctx = ConfigurationCtx(module=module)
    examples_config = parser.convert_examples_to_config(root, ctx)
    write_configuration(commands_config, 'commands', mod_path, output_path, profile, overwrite, compact)
    write_configuration(examples_config, 'examples', mod_path, output_path, profile, overwrite, compact)


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


def write_configuration(data, file_name, mod_path, output_dir, profile, overwrite, compact):
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
