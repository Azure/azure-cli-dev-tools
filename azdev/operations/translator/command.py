from knack.util import CLIError
from knack.help_files import _load_help_file
from knack.help import HelpExample

import types

from .utilities import AZDevTransDeprecateInfo, check_validator


DEFAULT_NO_WAIT_PARAM_DEST = 'no_wait'


class AZDevTransCommandHelp:

    def __init__(self, description, help_data):
        try:
            self.short_summary = description[:description.index('.')]
            long_summary = description[description.index('.') + 1:].lstrip()
            self.long_summary = ' '.join(long_summary.splitlines())
        except (ValueError, AttributeError):
            self.short_summary = description

        if help_data:
            assert help_data['type'].lower() == 'command'
            short_summary = help_data.get('short-summary', None)
            long_summary = help_data.get('long-summary', None)
            if short_summary:
                self.short_summary = short_summary
            if long_summary:
                self.long_summary = long_summary
            assert self.short_summary


class AZDevTransCommand:
    # supported: 'confirmation', 'no_wait_param', 'supports_no_wait', 'is_preview', 'preview_info', 'is_experimental', 'experimental_info', 'deprecate_info',
    # 'table_transformer', 'exception_handler', 'client_factory', 'transform', 'validator', 'supports_local_cache', 'min_api', 'max_api',

    # PendingForDeprecation: 'client_arg_name', 'model_path', 'resource_type', 'operation_group',
    # TODO: parse operation combine operation template and function name

    # ignored: 'doc_string_source', 'local_context_attribute', 'custom_command_type', 'command_type',

    def __init__(self, name, parent_group, full_name, table_instance):
        self.name = name
        self.parent_group = parent_group
        self.full_name = full_name

        self.sub_arguments = {}

        self._parse_deprecate_info(table_instance)
        self._parse_is_preview(table_instance)
        self._parse_is_experimental(table_instance)
        assert not (self.is_preview and self.is_experimental)

        self._parse_confirmation(table_instance)
        self._parse_no_wait(table_instance)

        self._parse_min_api(table_instance)
        self._parse_max_api(table_instance)
        self._parse_resource_type(table_instance)
        self._parse_operation_group(table_instance)

        self._parse_client_arg_name(table_instance)

        self._parse_supports_local_cache(table_instance)
        self._parse_model_path(table_instance)

        self._parse_operation(table_instance)
        self._parse_client_factory(table_instance)

        self._parse_validator(table_instance)
        self._parse_transform(table_instance)
        self._parse_table_transformer(table_instance)
        self._parse_exception_handler(table_instance)

        self._parse_help(table_instance)

    def _parse_deprecate_info(self, table_instance):
        deprecate_info = table_instance.deprecate_info
        if deprecate_info is not None:
            deprecate_info = AZDevTransDeprecateInfo(deprecate_info)
        self.deprecate_info = deprecate_info

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
        if table_instance.confirmation:
            self.confirmation = True
        else:
            self.confirmation = False

    def _parse_no_wait(self, table_instance):
        self.no_wait_param = None
        if table_instance.supports_no_wait:
            self.no_wait_param = DEFAULT_NO_WAIT_PARAM_DEST
        if table_instance.no_wait_param:
            self.no_wait_param = table_instance.no_wait_param

    def _parse_operation(self, table_instance):
        from azure.cli.core.commands.command_operation import BaseCommandOperation
        command_operation = table_instance.command_kwargs.get('command_operation', None)
        if not isinstance(command_operation, BaseCommandOperation):
            raise TypeError('Command operation is not an instant of "BaseCommandOperation", get "{}"'.format(
                type(command_operation)))
        self.operation = command_operation

    def _parse_client_factory(self, table_instance):
        from azure.cli.core.translator.client_factory import AzClientFactory
        client_factory = table_instance.command_kwargs.get('client_factory', None)
        if client_factory is not None:
            if not isinstance(client_factory, AzClientFactory):
                raise TypeError('Client factory is not an instance of "AzClientFactory", get "{}"'.format(
                    type(client_factory)))
        else:
            # print('\t "{}" has no client factory'.format(self.full_name))
            pass
        self.client_factory = client_factory

    def _parse_validator(self, table_instance):
        validator = table_instance.validator
        check_validator(validator)
        self.validator = validator

    def _parse_transform(self, table_instance):
        from azure.cli.core.translator.transformer import AzTransformer
        transform = table_instance.command_kwargs.get('transform', None)
        if transform is not None:
            if not isinstance(transform, AzTransformer):
                raise TypeError('Transform is not an instance of "AzTransformer", get "{}"'.format(
                    type(transform)))
        self.transform = transform

    def _parse_table_transformer(self, table_instance):
        from azure.cli.core.translator.transformer import AzTransformer
        table_transformer = table_instance.table_transformer
        if isinstance(table_transformer, str):
            table_transformer = table_transformer.strip()
            if not table_transformer:
                table_transformer = None
        if table_transformer is not None:
            if not isinstance(table_transformer, str) and not isinstance(table_transformer, AzTransformer):
                raise TypeError('Table transform is not a string or an instance of "AzTransformer", get "{}"'.format(
                    type(table_transformer)))
        self.table_transformer = table_transformer

    def _parse_exception_handler(self, table_instance):
        from azure.cli.core.translator.exception_handler import AzExceptionHandler
        exception_handler = table_instance.exception_handler
        if exception_handler is not None:
            if not isinstance(exception_handler, AzExceptionHandler):
                raise TypeError('Exception handler is not an instance of "AzExceptionHandler", get "{}"'.format(
                    type(exception_handler)))
        self.exception_handler = exception_handler

    def _parse_client_arg_name(self, table_instance):
        # TODO: Deprecate this parameter, because it's only for eventgrid track1 SDK usage
        client_arg_name = table_instance.command_kwargs.get('client_arg_name', None)
        assert client_arg_name is None or isinstance(client_arg_name, str)
        if client_arg_name is not None:
            if client_arg_name == 'client':
                client_arg_name = None
        self.client_arg_name = client_arg_name

    def _parse_supports_local_cache(self, table_instance):
        supports_local_cache = table_instance.command_kwargs.get('supports_local_cache', False)
        assert isinstance(supports_local_cache, bool)
        self.supports_local_cache = supports_local_cache

    def _parse_model_path(self, table_instance):
        # TODO: Deprecate this parameter, Only `network front-door waf-policy` command group used.
        model_path = table_instance.command_kwargs.get('model_path', None)
        assert model_path is None or isinstance(model_path, str)
        self.model_path = model_path

    def _parse_min_api(self, table_instance):
        min_api = table_instance.command_kwargs.get('min_api', None)
        assert min_api is None or isinstance(min_api, str)
        self.min_api = min_api

    def _parse_max_api(self, table_instance):
        max_api = table_instance.command_kwargs.get('max_api', None)
        assert max_api is None or isinstance(max_api, str)
        self.max_api = max_api

    def _parse_resource_type(self, table_instance):
        from azure.cli.core.profiles import ResourceType, CustomResourceType, PROFILE_TYPE
        resource_type = table_instance.command_kwargs.get('resource_type', None)
        if resource_type is not None:
            if isinstance(resource_type, ResourceType):
                pass
            elif isinstance(resource_type, CustomResourceType):
                # used for extensions. it will call register_resource_type.
                pass
            elif resource_type == PROFILE_TYPE:
                # used only in commands: ad sp | ad app | feature
                # TODO: Deprecate this value. Don't need this for profile specific configuration
                raise NotImplementedError()
            else:
                raise TypeError("Not supported resource_type type {}".format(type(resource_type)))
        self.resource_type = resource_type

    def _parse_operation_group(self, table_instance):
        operation_group = table_instance.command_kwargs.get('operation_group', None)
        assert operation_group is None or isinstance(operation_group, str)
        self.operation_group = operation_group

    def _parse_help(self, table_instance):
        description = table_instance.description
        if callable(description):
            description = description()
        assert isinstance(description, str)
        help_data = _load_help_file(self.full_name)
        self.help = AZDevTransCommandHelp(description, help_data)

        examples = None
        if help_data:
            if 'examples' in help_data:
                examples = [HelpExample(d) for d in help_data['examples']]
            elif 'example' in help_data:
                examples = [HelpExample(d) for d in help_data['example']]
        self.examples = examples

        parameters_help_data = {}
        if help_data:
            if 'parameters' in help_data:
                for parameter in help_data['parameters']:
                    parameters_help_data[parameter['name']] = parameter
        self.parameters_help_data = parameters_help_data
