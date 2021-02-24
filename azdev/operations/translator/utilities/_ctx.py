# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections import defaultdict

from knack.cli import CLI
from knack.util import CLIError

default_core_reference = {
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


class _Invocation(object):

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
        self.invocation = _Invocation()

    def get_cli_version(self):
        from azure.cli.core import __version__
        return __version__

    def _should_enable_color(self):
        return False


class AZDevTransConfigurationCtx:

    def __init__(self, cli_ctx, module, reference=default_core_reference):
        self._cli_ctx = cli_ctx
        self._arg_type_reference_format_queue = []
        self._command_sdk_queue = []
        self._output_arg_types = set()
        self._module_name = module.__name__
        self.used_reference = {}
        self._reference = reference or {}
        self._reversed_reference = dict([(v, k) for k, v in self._reference.items()])
        assert len(self._reference) == len(self._reversed_reference)

    def set_art_type_reference_format(self, to_reference_format):
        assert isinstance(to_reference_format, bool)
        self._arg_type_reference_format_queue.append(to_reference_format)

    @property
    def art_type_reference_format(self):
        if len(self._arg_type_reference_format_queue) > 0:
            return self._arg_type_reference_format_queue[-1]
        else:
            raise ValueError('arg_type_reference_format_queue is empty')

    def unset_art_type_reference_format(self):
        if len(self._arg_type_reference_format_queue) > 0:
            self._arg_type_reference_format_queue.pop()
        else:
            raise ValueError('arg_type_reference_format_queue is empty')

    def set_command_sdk(self, sdk):
        self._command_sdk_queue.append(sdk)

    @property
    def current_command_sdk(self):
        if len(self._command_sdk_queue) > 0:
            command_sdk = self._command_sdk_queue[-1]
        else:
            command_sdk = None
        return command_sdk

    def unset_command_sdk(self):
        if len(self._command_sdk_queue) > 0:
            self._command_sdk_queue.pop()
        else:
            raise ValueError('command_resource_type_and_operation_group_queue is empty')

    def get_import_path(self, module_name, name):
        path = "{}#{}".format(module_name, name)
        return self.simplify_import_path(path)

    def add_output_arg_type(self, register_name):
        assert register_name not in self._output_arg_types
        self._output_arg_types.add(register_name)

    def is_output_arg_type(self, register_name):
        return register_name in self._output_arg_types

    def simplify_import_path(self, path):
        if path in self._reversed_reference:
            reference_name = self._reversed_reference[path]
            self.used_reference[reference_name] = path
            path = '${}'.format(reference_name)
        else:
            versioned_sdk_path = self.get_versioned_sdk_path()
            if versioned_sdk_path and path.startswith(versioned_sdk_path):
                path = path.replace(versioned_sdk_path, '@SDK')
            elif path.startswith(self._module_name):
                path = path.replace(self._module_name, '@')
        return path

    def get_operation_import_path(self, path):
        assert self.current_command_sdk is not None
        path = path.replace(self.current_command_sdk.resource_type.import_prefix, self.get_versioned_sdk_path())
        return self.simplify_import_path(path)

    def get_enum_import_path(self, module_name, name):
        path = "{}#{}".format(module_name, name)
        if self.current_command_sdk is not None:
            enum_cls = self.get_model(model_name=name)
            if enum_cls and str(enum_cls.__module__) == module_name:
                path = "{}.models#{}".format(self.get_versioned_sdk_path(), name)
            elif not enum_cls:
                print("Enum cannot find in SDK models, use full path: {}".format(path))
        return self.simplify_import_path(path)
    
    def get_model(self, model_name):
        from azure.cli.core.profiles import get_sdk
        resource_type = self.current_command_sdk.resource_type if self.current_command_sdk else None
        operation_group = self.current_command_sdk.operation_group if self.current_command_sdk else None
        return get_sdk(self._cli_ctx, resource_type, model_name, mod='models', operation_group=operation_group)

    def is_multi_api_sdk(self, resource_type):
        from azure.cli.core.profiles._shared import AZURE_API_PROFILES
        return bool(AZURE_API_PROFILES[self._cli_ctx.cloud.profile].get(resource_type, None))

    def get_api_version(self, resource_type, operation_group):
        from azure.cli.core.profiles._shared import _ApiVersions, get_api_version
        if not self.is_multi_api_sdk(resource_type):
            return None
        api_version = get_api_version(self._cli_ctx.cloud.profile, resource_type)
        if api_version is None:
            return None
        if isinstance(api_version, _ApiVersions):
            if operation_group is None:
                raise ValueError("operation_group is required for resource type '{}'".format(resource_type))
            api_version = getattr(api_version, operation_group)
        return api_version

    def get_versioned_sdk_path(self):
        if self.current_command_sdk is None:
            return None

        api_version = self.get_api_version(
            resource_type=self.current_command_sdk.resource_type,
            operation_group=self.current_command_sdk.operation_group)
        if not api_version:
            return self.current_command_sdk.resource_type.import_prefix

        return '{}.v{}'.format(
            self.current_command_sdk.resource_type.import_prefix,
            api_version.replace('-', '_').replace('.', '_')
        )
