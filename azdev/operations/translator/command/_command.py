# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.help_files import _load_help_file
from collections import OrderedDict
from azdev.operations.translator.utilities import build_deprecate_info, build_validator, AZDevTransNode
from ._help import build_command_help
from ._examples import build_command_examples
from ._client_factory import build_client_factory
from ._no_wait import build_command_no_wait
from ._operation import build_command_operation
from ._transform import build_command_transform
from ._table_transformer import build_command_table_transformer
from ._exception_handler import build_exception_handler
from ._sdk import build_command_sdk
from ._confirmation import build_command_confirmation


class AZDevTransCommand(AZDevTransNode):
    # supported: 'confirmation', 'no_wait_param', 'supports_no_wait', 'is_preview', 'preview_info', 'is_experimental', 'experimental_info', 'deprecate_info',
    # 'table_transformer', 'exception_handler', 'client_factory', 'transform', 'validator', 'supports_local_cache', 'min_api', 'max_api', 'resource_type', 'operation_group',

    # PendingForDeprecation: 'client_arg_name', 'model_path',
    # TODO: parse operation combine operation template and function name

    # ignored: 'doc_string_source', 'local_context_attribute', 'custom_command_type', 'command_type',

    def __init__(self, name, parent_group, full_name, table_instance):
        self.name = name
        self.parent_group = parent_group
        self.full_name = full_name
        self.registered_arg_types = {}

        self.sub_arguments = {}

        self._parse_deprecate_info(table_instance)
        self._parse_is_preview(table_instance)
        self._parse_is_experimental(table_instance)
        assert not (self.is_preview and self.is_experimental)

        self._parse_confirmation(table_instance)
        self._parse_no_wait(table_instance)

        self._parse_min_api(table_instance)
        self._parse_max_api(table_instance)
        self._parse_sdk(table_instance)
        # self._parse_resource_type(table_instance)
        # self._parse_operation_group(table_instance)

        self._parse_client_arg_name(table_instance)

        self._parse_supports_local_cache(table_instance)
        self._parse_model_path(table_instance)

        self._parse_operation(table_instance)
        self._parse_client_factory(table_instance)

        self._parse_validator(table_instance)
        self._parse_transform(table_instance)
        self._parse_table_transformer(table_instance)
        self._parse_exception_handler(table_instance)

        self._parse_help_and_examples(table_instance)

    def _parse_deprecate_info(self, table_instance):
        deprecate_info = table_instance.deprecate_info
        self.deprecate_info = build_deprecate_info(deprecate_info)

    def _parse_is_preview(self, table_instance):
        if table_instance.preview_info:
            self.is_preview = True
        else:
            self.is_preview = False

    def _parse_is_experimental(self, table_instance):
        if table_instance.experimental_info:
            self.is_experimental = True
        else:
            self.is_experimental = False

    def _parse_confirmation(self, table_instance):
        self.confirmation = build_command_confirmation(table_instance.confirmation)

    def _parse_no_wait(self, table_instance):
        self.no_wait = build_command_no_wait(table_instance.supports_no_wait, table_instance.no_wait_param)

    def _parse_operation(self, table_instance):
        command_operation = table_instance.command_kwargs.get('command_operation', None)
        self.operation = build_command_operation(command_operation)

    def _parse_client_factory(self, table_instance):
        client_factory = table_instance.command_kwargs.get('client_factory', None)
        self.client_factory = build_client_factory(client_factory)

    def _parse_validator(self, table_instance):
        validator = table_instance.validator
        self.validator = build_validator(validator)

    def _parse_transform(self, table_instance):
        transform = table_instance.command_kwargs.get('transform', None)
        self.transform = build_command_transform(transform)

    def _parse_table_transformer(self, table_instance):
        table_transformer = table_instance.table_transformer
        self.table_transformer = build_command_table_transformer(table_transformer)

    def _parse_exception_handler(self, table_instance):
        exception_handler = table_instance.exception_handler
        self.exception_handler = build_exception_handler(exception_handler)

    def _parse_supports_local_cache(self, table_instance):
        supports_local_cache = table_instance.command_kwargs.get('supports_local_cache', False)
        assert isinstance(supports_local_cache, bool)
        self.supports_local_cache = supports_local_cache

    def _parse_min_api(self, table_instance):
        min_api = table_instance.command_kwargs.get('min_api', None)
        assert min_api is None or isinstance(min_api, str)
        self.min_api = min_api

    def _parse_max_api(self, table_instance):
        max_api = table_instance.command_kwargs.get('max_api', None)
        assert max_api is None or isinstance(max_api, str)
        self.max_api = max_api

    def _parse_sdk(self, table_instance):
        resource_type = table_instance.command_kwargs.get('resource_type', None)
        if resource_type is None:
            print('ResourceType miss: "{}"'.format(self.full_name))
        operation_group = table_instance.command_kwargs.get('operation_group', None)
        self.sdk = build_command_sdk(resource_type, operation_group)

    def _parse_help_and_examples(self, table_instance):
        description = table_instance.description
        if callable(description):
            description = description()

        assert isinstance(description, str)
        help_data = _load_help_file(self.full_name)
        self.help = build_command_help(description, help_data)
        if not self.help:
            print('Command "{}" miss help.'.format(self.full_name))

        examples = None
        if help_data:
            if 'examples' in help_data:
                examples = help_data['examples']
            elif 'example' in help_data:
                examples = help_data['example']
        self.examples = build_command_examples(examples)

        parameters_help_data = {}
        if help_data:
            if 'parameters' in help_data:
                for parameter in help_data['parameters']:
                    parameters_help_data[parameter['name']] = parameter
        self.parameters_help_data = parameters_help_data

    def _parse_model_path(self, table_instance):
        # TODO: Deprecate this parameter, Only `network front-door waf-policy` command group used.
        model_path = table_instance.command_kwargs.get('model_path', None)
        assert model_path is None or isinstance(model_path, str)
        self.model_path = model_path

    def _parse_client_arg_name(self, table_instance):
        # TODO: Deprecate this parameter, because it's only for eventgrid track1 SDK usage
        client_arg_name = table_instance.command_kwargs.get('client_arg_name', None)
        assert client_arg_name is None or isinstance(client_arg_name, str)
        if client_arg_name is not None:
            if client_arg_name == 'client':
                client_arg_name = None
        self.client_arg_name = client_arg_name

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

        if self.min_api:
            value['min-api'] = self.min_api
        if self.max_api:
            value['max-api'] = self.max_api

        if self.help:
            k, v = self.help.to_config(ctx)
            value[k] = v

        if self.sdk:
            k, v = self.sdk.to_config(ctx)
            value[k] = v

        if self.operation:
            k, v = self.operation.to_config(ctx)
            value[k] = v
        if self.client_factory:
            k, v = self.client_factory.to_config(ctx)
            value[k] = v
        if self.client_arg_name:
            value['client-arg-name'] = self.client_arg_name

        if self.confirmation:
            k, v = self.confirmation.to_config(ctx)
            value[k] = v
        if self.no_wait:
            k, v = self.no_wait.to_config(ctx)
            value[k] = v

        if self.validator:
            k, v = self.validator.to_config(ctx)
            value[k] = v

        if self.transform:
            k, v = self.transform.to_config(ctx)
            value[k] = v

        if self.table_transformer:
            k, v = self.table_transformer.to_config(ctx)
            value[k] = v

        if self.exception_handler:
            k, v = self.exception_handler.to_config(ctx)
            value[k] = v

        if self.supports_local_cache:
            value['local-cache'] = self.supports_local_cache
        if self.model_path:
            value['model-path'] = self.model_path

        if self.registered_arg_types:
            output_arg_types = OrderedDict()
            for register_name in sorted(list(self.registered_arg_types.keys())):
                if ctx.is_output_arg_type(register_name):
                    continue
                arg_types = self.registered_arg_types[register_name]
                # TODO: checkout arg_types are same
                arg_type = [*arg_types.values()][0]
                ctx.set_art_type_reference_format(False)
                k, v = arg_type.to_config(ctx)
                output_arg_types[k] = v
                ctx.unset_art_type_reference_format()
                ctx.add_output_arg_type(register_name)
            if len(output_arg_types) > 0:
                value['argument-types'] = output_arg_types

        if self.sub_arguments:
            ctx.set_command_sdk(sdk=self.sdk)
            arguments = OrderedDict()
            for arg_name in sorted(list(self.sub_arguments.keys())):
                k, v = self.sub_arguments[arg_name].to_config(ctx)
                arguments[k] = v
            ctx.unset_command_sdk()
            value['arguments'] = arguments

        return key, value

    def to_example_config(self, ctx):
        key = self.name
        if self.examples:
            _, value = self.examples.to_config(ctx)
        else:
            value = []
        return key, value


def build_command(name, parent_group, full_name, table_instance):
    return AZDevTransCommand(name, parent_group, full_name, table_instance)
