# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azdev.operations.translator.utilities import build_deprecate_info, AZDevTransNode
from knack.help import _load_help_file
from collections import OrderedDict
from ._help import build_command_group_help


class AZDevTransCommandGroup(AZDevTransNode):
    # supported: 'is_preview', 'preview_info', 'is_experimental', 'experimental_info', 'operations_tmpl'

    # Ignored: 'custom_command_type', 'command_type',  'local_context_attribute', 'command_type',
    # 'custom_command_type', 'transform', 'validator', 'exception_handler', 'supports_no_wait', 'min_api', 'max_api',
    # 'resource_type', 'operation_group', 'client_factory'

    UNDEFINED_SDK = ""

    def __init__(self, name, parent_group, full_name, table_instance):
        self.name = name
        self.parent_group = parent_group
        self.full_name = full_name
        self.registered_arg_types = {}
        self.sdk = self.UNDEFINED_SDK

        self.sub_groups = {}
        self.sub_commands = {}

        if not table_instance:
            table_instance = None

        self._parse_deprecate_info(table_instance)
        self._parse_is_preview(table_instance)
        self._parse_is_experimental(table_instance)
        assert not (self.is_preview and self.is_experimental)

        self._parse_operations_tmpl(table_instance)
        self._parse_help(table_instance)

    def _parse_deprecate_info(self, table_instance):
        deprecate_info = table_instance.group_kwargs.get('deprecate_info', None) if table_instance else None
        self.deprecate_info = build_deprecate_info(deprecate_info)

    def _parse_is_preview(self, table_instance):
        is_preview = table_instance.group_kwargs.get('is_preview', False) if table_instance else False
        assert isinstance(is_preview, bool)
        self.is_preview = is_preview

    def _parse_is_experimental(self, table_instance):
        is_experimental = table_instance.group_kwargs.get('is_experimental', False) if table_instance else False
        assert isinstance(is_experimental, bool)
        self.is_experimental = is_experimental

    def _parse_operations_tmpl(self, table_instance):
        operations_tmpl = table_instance.operations_tmpl if table_instance else None
        assert operations_tmpl is None or isinstance(operations_tmpl, str)
        self.operations_tmpl = operations_tmpl

    def _parse_help(self, table_instance):
        if table_instance is None:
            hp = None
        else:
            help_data = _load_help_file(self.full_name)
            if help_data is None:
                print('Command group: "{}" miss help data.'.format(self.full_name))
                hp = None
            else:
                hp = build_command_group_help(help_data)
        self.help = hp

    def to_config(self, ctx):
        key = self.name
        value = OrderedDict()
        if self.full_name:
            value["full-name"] = self.full_name

        if self.deprecate_info:
            k, v = self.deprecate_info.to_config(ctx)
            value[k] = v

        if self.is_preview:
            value['preview'] = self.is_preview
        if self.is_experimental:
            value['experimental'] = self.is_experimental

        if self.help:
            k, v = self.help.to_config(ctx)
            value[k] = v

        if self.sdk:
            k, v = self.sdk.to_config(ctx)
            value[k] = v

        if self.registered_arg_types:
            ctx.set_command_sdk(sdk=self.sdk)
            output_arg_types = OrderedDict()
            for register_name in sorted(list(self.registered_arg_types.keys())):
                if ctx.is_output_arg_type(register_name):
                    continue
                arg_types = self.registered_arg_types[register_name]
                if len(arg_types) == 1:
                    continue
                # TODO: checkout arg_types are same
                arg_type = [*arg_types.values()][0]
                ctx.set_art_type_reference_format(False)
                k, v = arg_type.to_config(ctx)
                output_arg_types[k] = v
                ctx.unset_art_type_reference_format()
                ctx.add_output_arg_type(register_name)
            ctx.unset_command_sdk()
            if len(output_arg_types) > 0:
                value['argument-types'] = output_arg_types

        if self.sub_commands:
            ctx.set_command_sdk(sdk=self.sdk)
            sub_commands = OrderedDict()
            for sub_command_name in sorted(list(self.sub_commands.keys())):
                k, v = self.sub_commands[sub_command_name].to_config(ctx)
                if v is None:
                    continue
                sub_commands[k] = v
            ctx.unset_command_sdk()
            if len(sub_commands) > 0:
                value['commands'] = sub_commands

        if self.sub_groups:
            ctx.set_command_sdk(sdk=self.sdk)
            sub_groups = OrderedDict()
            for sub_group_name in sorted(list(self.sub_groups.keys())):
                k, v = self.sub_groups[sub_group_name].to_config(ctx)
                if v is None:
                    continue
                sub_groups[k] = v
            ctx.unset_command_sdk()
            if len(sub_groups) > 0:
                value['command-groups'] = sub_groups

        if 'commands' not in value and 'command-groups' not in value:
            return key, None
        return key, value

    def to_example_config(self, ctx):
        key = self.name
        value = OrderedDict()

        if self.sub_commands:
            sub_commands = OrderedDict()
            for sub_command_name in sorted(list(self.sub_commands.keys())):
                k, v = self.sub_commands[sub_command_name].to_example_config(ctx)
                if v is None:
                    continue
                sub_commands[k] = v
            if len(sub_commands) > 0:
                value['commands'] = sub_commands

        if self.sub_groups:
            sub_groups = OrderedDict()
            for sub_group_name in sorted(list(self.sub_groups.keys())):
                k, v = self.sub_groups[sub_group_name].to_example_config(ctx)
                if v is None:
                    continue
                sub_groups[k] = v
            if len(sub_groups) > 0:
                value['command-groups'] = sub_groups
        if 'commands' not in value and 'command-groups' not in value:
            return key, None
        return key, value


def build_command_group(name, parent_group, full_name, table_instance):
    return AZDevTransCommandGroup(name, parent_group, full_name, table_instance)
