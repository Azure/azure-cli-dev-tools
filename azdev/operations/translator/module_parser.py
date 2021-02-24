# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import defaultdict, OrderedDict
from knack.commands import CLICommandsLoader
from knack.util import CLIError
from knack.arguments import ArgumentRegistry

from azdev.operations.translator.argument import build_argument
from azdev.operations.translator.command import build_command
from azdev.operations.translator.command_group import build_command_group
from azdev.operations.translator.arg_type import AZDevTransRegisteredArgType
import datetime


class AZDevTransModuleParser(CLICommandsLoader):

    VERSION = "0.1.0"

    def __init__(self, cli_ctx=None, **kwargs):
        cli_ctx = cli_ctx
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
        if not command_loader.supported_resource_type():
            raise CLIError('Not supported resource type "{}" for current profile "{}"'.format(
                command_loader._get_resource_type(), self.cli_ctx.cloud.profile))
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
        config['version'] = self.VERSION
        config['created'] = str(datetime.datetime.now())
        if ctx.imports:
            config['imports'] = ctx.imports
        k, v = root.to_config(ctx)
        config[k] = v
        return config

    def convert_examples_to_config(self, root, ctx):
        k, v = root.to_example_config(ctx)
        config = OrderedDict()
        config['version'] = self.VERSION
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

        command_sdk_counter = {}
        for sub_command_name, sub_command_group in parent_group.sub_groups.items():
            sdk = sub_command_group.sdk
            if sdk not in command_sdk_counter:
                command_sdk_counter[sdk] = 0
            command_sdk_counter[sdk] += 1
        max_count = 0
        for sdk, count in command_sdk_counter.items():
            if count > max_count:
                max_count = count
                parent_group.sdk = sdk

        # register arg_types used in sub command groups
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

        # setup parent_group resource_type and operation_group by sub commands if they are not defined
        if parent_group.sdk == parent_group.UNDEFINED_SDK:
            command_sdk_counter = {}
            for sub_command_name, sub_command in parent_group.sub_commands.items():
                sdk = sub_command.sdk
                if sdk not in command_sdk_counter:
                    command_sdk_counter[sdk] = 0
                command_sdk_counter[sdk] += 1
            max_count = 0
            for sdk, count in command_sdk_counter.items():
                if count > max_count:
                    max_count = count
                    parent_group.sdk = sdk

        # register arg_types used in sub commands
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
            if arg.arg_type is not None and isinstance(arg.arg_type, AZDevTransRegisteredArgType):
                arg_type = arg.arg_type
                if arg_type.register_name not in registered_arg_types:
                    registered_arg_types[arg_type.register_name] = {}
                registered_arg_types[arg_type.register_name][arg_name] = arg_type
