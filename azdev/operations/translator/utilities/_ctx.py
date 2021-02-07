# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections import defaultdict

from knack.cli import CLI
from knack.util import CLIError

default_core_imports = {
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

    def __init__(self, module, imports=None):
        self._arg_type_reference_format_queue = []
        self._output_arg_types = set()
        self._module_name = module.__name__
        self.imports = imports or {}
        self._reversed_imports = dict([(v, k) for k, v in self.imports.items()])
        assert len(self.imports) == len(self._reversed_imports)

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

    def get_import_path(self, module_name, name):
        path = "{}#{}".format(module_name, name)
        return self.simplify_import_path(path)

    def add_output_arg_type(self, register_name):
        assert register_name not in self._output_arg_types
        self._output_arg_types.add(register_name)

    def is_output_arg_type(self, register_name):
        return register_name in self._output_arg_types

    def simplify_import_path(self, path):
        if path in self._reversed_imports:
            path = '${}'.format(self._reversed_imports[path])
        elif path.startswith(self._module_name):
            path = path.replace(self._module_name, '')
        return path

    def get_enum_import_path(self, module_name, name):
        # TODO: Checkout module_name
        path = name
        return path
