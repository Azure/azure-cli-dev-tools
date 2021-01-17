# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import importlib
import os
from collections import defaultdict
import types

from knack.cli import CLI
from knack.commands import CLICommandsLoader
from knack.log import get_logger
from knack.util import CLIError, ensure_dir
from knack.deprecation import Deprecated
from knack.arguments import ArgumentRegistry

from azdev.operations.extensions import list_extensions
from azdev.utilities import get_cli_repo_path


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
        self.object_type = table_instance.object_type
        self.target = table_instance.target

        self.redirect = table_instance.redirect
        self.hide = table_instance.hide
        self.expiration = table_instance.expiration

        self.tag_template = table_instance._get_tag(self._PLACEHOLDER_INSTANCE)
        self.message_template = table_instance._get_message(self._PLACEHOLDER_INSTANCE)

# command_group_set = set()


class AZDevTransCommandGroup:

    # supported: 'is_preview', 'preview_info', 'is_experimental', 'experimental_info', 'operations_tmpl'
    # 'min_api', 'max_api', 'resource_type', 'operation_group', 'custom_command_type', 'command_type',  'local_context_attribute'

    def __init__(self, name, parent_group, full_name, table_instance):
        self.name = name
        self.parent_group = parent_group
        self.full_name = full_name

        self.sub_groups = {}
        self.sub_commands = {}

        if not table_instance:
            table_instance = None

        self._parse_deprecate_info(table_instance)
        self._parse_is_preview(table_instance)
        self._parse_is_experimental(table_instance)
        assert not (self.is_preview and self.is_experimental)

        self._parse_operations_tmpl(table_instance)

    def _parse_deprecate_info(self, table_instance):
        if table_instance is None:
            deprecate_info = None
        else:
            deprecate_info = table_instance.group_kwargs.get('deprecate_info', None)
        if deprecate_info is not None:
            deprecate_info = AZDevTransDeprecateInfo(deprecate_info)
        self.deprecate_info = deprecate_info

    def _parse_is_preview(self, table_instance):
        if table_instance is None:
            is_preview = False
        else:
            is_preview = table_instance.group_kwargs.get('is_preview', False)
        assert isinstance(is_preview, bool)
        self.is_preview = is_preview

    def _parse_is_experimental(self, table_instance):
        if table_instance is None:
            is_experimental = False
        else:
            is_experimental = table_instance.group_kwargs.get('is_experimental', False)
        assert isinstance(is_experimental, bool)
        self.is_experimental = is_experimental

    def _parse_operations_tmpl(self, table_instance):
        if table_instance is None:
            operations_tmpl = None
        else:
            operations_tmpl = table_instance.operations_tmpl
        assert operations_tmpl is None or isinstance(operations_tmpl, str)
        self.operations_tmpl = operations_tmpl


DEFAULT_NO_WAIT_PARAM_DEST = 'no_wait'

# command_set


class AZDevTransCommand:
    # supported: 'confirmation', 'no_wait_param', 'supports_no_wait', 'is_preview', 'preview_info', 'is_experimental', 'experimental_info', 'deprecate_info',
    # 'table_transformer', 'exception_handler', 'client_factory', 'transform', 'validator', 'supports_local_cache', 'min_api', 'max_api',

    # PendingForDeprecation: 'client_arg_name', 'model_path', 'resource_type', 'operation_group',
    # 'custom_command_type', 'command_type',

    # TODO: parse operation combine operation template and function name

    # ignored: 'doc_string_source', 'local_context_attribute'

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

        self._parse_client_factory(table_instance)  # TODO:
        # self._parse_operations_tmpl(table_instance)     # TODO:
        self._parse_validator(table_instance)   # TODO:
        self._parse_transform(table_instance)   # TODO:
        self._parse_table_transformer(table_instance)   # TODO:
        self._parse_exception_handler(table_instance)   # TODO:

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

    def _parse_client_factory(self, table_instance):
        client_factory = table_instance.command_kwargs.get('client_factory', None)
        if client_factory is not None:
            if isinstance(client_factory, types.FunctionType):
                # TODO: convert to string
                pass
            else:
                raise CLIError('Not supported client_factory type {}'.format(type(client_factory)))
        self.client_factory = client_factory

    # def _parse_operations_tmpl(self, table_instance):
    #     operations_tmpl = table_instance.command_kwargs.get('operations_tmpl', None)
    #     if operations_tmpl is None:
    #         print(operations_tmpl)
    #     assert operations_tmpl is None or isinstance(operations_tmpl, str)
    #     self.operations_tmpl = operations_tmpl

    def _parse_validator(self, table_instance):
        validator = table_instance.validator
        if validator is not None:
            if isinstance(validator, types.FunctionType):
                # TODO: convert to string
                pass
            else:
                raise CLIError("Not Support validator type {}".format(type(validator)))
        self.validator = validator

    def _parse_transform(self, table_instance):
        transform = table_instance.command_kwargs.get('transform', None)
        if transform is not None:
            if isinstance(transform, types.FunctionType):
                # TODO: convert to string
                pass
            else:
                # TODO: convert callable instance to string
                # DeploymentOutputLongRunningOperation etc
                pass
        self.transform = transform

    def _parse_table_transformer(self, table_instance):
        table_transformer = table_instance.table_transformer
        if table_transformer is not None:
            if isinstance(table_transformer, types.FunctionType):
                # TODO: convert table_transformer to string
                pass
            elif isinstance(table_transformer, str):
                # TODO:
                pass
            else:
                raise CLIError('Invalid table_transformer type {}'.format(type(table_transformer)))
        self.table_transformer = table_transformer

    def _parse_exception_handler(self, table_instance):
        exception_handler = table_instance.exception_handler
        if exception_handler is not None:
            if isinstance(exception_handler, types.FunctionType):
                # TODO: convert to string
                pass
            else:
                raise CLIError('Not supported exception_handler type {}'.format(type(exception_handler)))
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
                # TODO: convert to string
                pass
            elif isinstance(resource_type, CustomResourceType):
                # TODO: convert to string
                pass
            elif resource_type == PROFILE_TYPE:
                # used only in commands: ad sp | ad app | feature
                # TODO: Deprecate this value. Don't need this for profile specific configuration
                pass
            else:
                raise CLIError("Not supported resource_type type {}".format(type(resource_type)))
        self.resource_type = resource_type

    def _parse_operation_group(self, table_instance):
        operation_group = table_instance.command_kwargs.get('operation_group', None)
        assert operation_group is None or isinstance(operation_group, str)
        self.operation_group = operation_group

    # def _parse_custom_command_type(self):


class AZDevTransArgument:
    # supported: 'deprecate_info', 'is_preview', 'is_experimental', 'dest', 'help', 'options_list', 'action', 'arg_group', 'arg_type', 'choices', 'default', 'completer', 'configured_default', 'const', 'id_part', 'local_context_attribute', 'max_api', 'min_api', 'nargs',  'required', 'type', 'validator'
    # ignored: 'metavar', 'operation_group', 'resource_type', 'dest'
    # invalid: 'option_list', 'metave', ' FilesCompleter'
    # TODO CHECK: option_strings, default_value_source, custom_command_type, command_type

    def __init__(self, name, parent_command, table_instance):
        self.name = name
        self.parent_command = parent_command

        type_settings = table_instance.type.settings
        # unwrap arg_type settings
        while 'arg_type' in type_settings:
            arg_type = type_settings.pop('arg_type', None)
            for key, value in arg_type.settings.items():
                if key not in type_settings:
                    type_settings[key] = value

        self._parse_deprecate_info(type_settings)
        self._parse_is_preview(type_settings)
        self._parse_is_experimental(type_settings)
        assert not (self.is_preview and self.is_experimental)

        self._parse_dest(type_settings)
        self._parse_help(type_settings)
        self._parse_options_list(type_settings)
        self._parse_arg_group(type_settings)
        self._parse_choices(type_settings)
        self._parse_default(type_settings)
        self._parse_id_part(type_settings)

        self._parse_max_api(type_settings)
        self._parse_min_api(type_settings)

        self._parse_nargs(type_settings)
        self._parse_required(type_settings)
        self._parse_configured_default(type_settings)

        self._parse_action(type_settings)   # TODO:
        self._parse_const(type_settings)

        self._parse_completer(type_settings)    # TODO:
        self._parse_local_context_attribute(type_settings)  # TODO:
        self._parse_type(type_settings)         # TODO:
        self._parse_validator(type_settings)    # TODO:

    def _parse_deprecate_info(self, type_settings):
        deprecate_info = type_settings.get('deprecate_info', None)
        if deprecate_info is not None:
            deprecate_info = AZDevTransDeprecateInfo(deprecate_info)
        self.deprecate_info = deprecate_info

    def _parse_dest(self, type_settings):
        dest = type_settings.get('dest', None)
        assert dest == self.name

    def _parse_help(self, type_settings):
        help = type_settings.get('help', None)
        assert help is None or isinstance(help, str)
        self.help = help

    def _parse_options_list(self, type_settings):
        options_list = type_settings.get('options_list', None)
        if options_list is not None:
            assert isinstance(options_list, (list, tuple))
            converted_options_list = []
            for idx in range(len(options_list)):
                option = options_list[idx]
                if not isinstance(option, str):
                    assert isinstance(option, Deprecated)
                    option = AZDevTransDeprecateInfo(option)
                converted_options_list.append(option)
            options_list = converted_options_list
            if len(options_list) == 0:
                options_list = None
        self.options_list = options_list

    def _parse_arg_group(self, type_settings):
        arg_group = type_settings.get('arg_group', None)
        if arg_group == '':
            arg_group = None
        assert arg_group is None or isinstance(arg_group, str)
        self.arg_group = arg_group

    def _parse_choices(self, type_settings):
        choices = type_settings.get('choices', None)
        if choices is not None:
            for value in choices:
                assert isinstance(value, (str, int)), 'type is {}'.format(type(value))
        self.choices = choices

    def _parse_default(self, type_settings):
        default = type_settings.get('default', None)
        if default == '':
            default = None

        if default is not None:
            if isinstance(default, bool):
                default = str(default)
            if self.choices is not None:
                if isinstance(default, list):
                    for value in default:
                        assert value in self.choices
                else:
                    assert default in self.choices
        self.default = default

    def _parse_configured_default(self, type_settings):
        configured_default = type_settings.get('configured_default', None)
        if configured_default == '':
            configured_default = None
        assert configured_default is None or isinstance(configured_default, str)
        self.configured_default = configured_default

    def _parse_const(self, type_settings):
        const = type_settings.get('const', None)
        if const == '':
            const = None
        if const is not None:
            assert self.action is not None and 'const' in self.action
            assert isinstance(const, (str, int))
        self.const = const

    def _parse_id_part(self, type_settings):
        id_part = type_settings.get('id_part', None)
        if id_part == '':
            id_part = None
        assert id_part is None or isinstance(id_part, str)
        self.id_part = id_part

    def _parse_is_preview(self, type_settings):
        is_preview = type_settings.get('is_preview', False)
        assert isinstance(is_preview, bool)
        self.is_preview = is_preview

    def _parse_is_experimental(self, type_settings):
        is_experimental = type_settings.get('is_experimental', False)
        assert isinstance(is_experimental, bool)
        self.is_experimental = is_experimental

    def _parse_max_api(self, type_settings):
        max_api = type_settings.get('max_api', None)
        assert max_api is None or isinstance(max_api, str)
        self.max_api = max_api

    def _parse_min_api(self, type_settings):
        min_api = type_settings.get('min_api', None)
        assert min_api is None or isinstance(min_api, str)
        self.min_api = min_api

    def _parse_nargs(self, type_settings):
        nargs = type_settings.get('nargs', None)
        if nargs == '':
            nargs = None
        assert nargs is None or isinstance(nargs, int) or nargs in ['?', '*', '+']
        self.nargs = nargs

    def _parse_required(self, type_settings):
        required = type_settings.get('required', False)
        assert isinstance(required, bool)
        self.required = required

    def _parse_action(self, type_settings):
        action = type_settings.get('action', None)
        if action is not None:
            if not isinstance(action, str):
                # TODO: convert class type instance to string
                pass
        self.action = action

    def _parse_completer(self, type_settings):
        completer = type_settings.get('completer', None)
        if completer is not None:
            # TODO: convert completer to string
            pass
        self.completer = completer

    def _parse_local_context_attribute(self, type_settings):
        from azure.cli.core.local_context import LocalContextAttribute
        local_context_attribute = type_settings.get('local_context_attribute', None)
        if local_context_attribute is not None:
            assert isinstance(local_context_attribute, LocalContextAttribute)
            # TODO: convert to AZDEVLocalContextAttribute
        self.local_context_attribute = local_context_attribute

    def _parse_type(self, type_settings):
        typ = type_settings.get('type', str)
        if typ not in (str, int, float, bool):
            if isinstance(typ, types.FunctionType):
                # TODO: convert to string
                pass
            elif isinstance(typ, types.MethodDescriptorType):
                # print(typ)
                # TODO: convert class method to string
                pass
            elif isinstance(typ, type):
                # print(typ)
                # TODO: convert class to string
                pass
            else:
                # SizeWithUnitConverter
                # TODO: convert callable instance to string
                # print(type(typ), typ)
                pass
        self.typ = typ

    def _parse_validator(self, type_settings):
        validator = type_settings.get('validator', None)
        if validator is not None:
            assert isinstance(validator, types.FunctionType)
            # TODO: Convert to string
        self.validator = validator


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
        # loader

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
                table_instance = self.command_table[full_name]
                command = AZDevTransCommand(
                    name=name, parent_group=parent_group, full_name=full_name,
                    table_instance=table_instance
                )
                self._add_sub_arguments(command=command, table_instance=table_instance)
                parent_group.sub_commands[name] = command

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
            command.sub_arguments[arg_name] = AZDevTransArgument(arg_name, parent_command=command, table_instance=arg)
            # try:
            #     command.sub_arguments[arg_name] = AZDevTransArgument(arg_name, parent_command=command, table_instance=arg)
            # except Exception as ex:
            #     raise CLIError("Parse argument '{}' failed for command '{}': {}".format(
            #         arg_name, command.full_name, ex
            #     ))


def generate_manual_config(mod_name, output_path=None, overwrite=False, profile='latest', is_extension=False):
    module, mod_path = _get_module(mod_name, is_extension)
    parser = AZDevTransModuleParser(profile=profile)
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


if __name__ == "__main__":
    def _get_all_mod_names():
        cli_path = get_cli_repo_path()
        command_modules_dir = os.path.join(cli_path, 'src', 'azure-cli', 'azure', 'cli', 'command_modules')
        my_list = os.listdir(command_modules_dir)
        print(my_list)
        mod_names = [mod_name for mod_name in my_list if os.path.isdir(os.path.join(command_modules_dir, mod_name))
                     and not mod_name.startswith('__')]
        return mod_names

    mod_names = _get_all_mod_names()
    values = set()
    for mod_name in mod_names:
        print(mod_name)
        generate_manual_config(mod_name)
    # print(sorted(list(_argument_keys)))

