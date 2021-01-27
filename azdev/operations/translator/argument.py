import types
from knack.deprecation import Deprecated
from knack.arguments import IgnoreAction
from collections import OrderedDict
from .utilities import AZDevTransDeprecateInfo, AZDevTransValidator, AZDevTransNode
import json
import argparse


class AZDevTransArgumentHelp(AZDevTransNode):

    def __init__(self, description, help_data):
        self.short_summary = help_data.get('short-summary', description)
        self.long_summary = help_data.get('long-summary', None)
        populator_commands = help_data.get('populator-commands', [])
        self.populator_commands = []
        if len(populator_commands) > 0:
            for command in populator_commands:
                assert isinstance(command, str)
                if command.startswith('`'):
                    command = command.strip('`')
                self.populator_commands.append(command)

    def to_config(self, ctx):
        key = 'help'
        value = OrderedDict()
        if self.short_summary:
            value['short-summary'] = self.short_summary
        if self.long_summary:
            value['long-summary'] = self.long_summary
        if self.populator_commands:
            value['populator-commands'] = self.populator_commands

        if set(value.keys()) == {"short-summary"}:
            value = value['short-summary']
        return key, value


class AZDevTransArgumentOptions(AZDevTransNode):

    def __init__(self, options_list):
        if not isinstance(options_list, (list, tuple)):
            raise TypeError('Expect list or tuple. Got "{}"'.format(type(options_list)))
        converted_options = {}
        for option in options_list:
            if not isinstance(option, str):
                if not isinstance(option, Deprecated):
                    raise TypeError('Expect Deprecated. Got "{}"'.format(type(option)))
                option = AZDevTransDeprecateInfo(option)
                option_str = option.target
            else:
                option_str = option
            if option_str in converted_options:
                raise TypeError('Duplicated value in options list: "{}"'.format(option_str))
            converted_options[option_str] = option
        self.options = converted_options

    def to_config(self, ctx):
        key = 'options'
        values = []
        for option_str in sorted(list(self.options.keys())):
            option = self.options[option_str]
            if isinstance(option, str):
                values.append(option)
            elif isinstance(option, AZDevTransDeprecateInfo):
                _, value = option.to_config(ctx)
                values.append(value)
        return key, values


class AZDevTransArgumentAction(AZDevTransNode):

    def __init__(self, action):
        from azure.cli.core.translator.action import AzAction, AzClsActionByFactory
        if not isinstance(action, str) and not issubclass(action, AzAction):
            raise TypeError("Expect str or AzAction type, got '{}'".format(action))
        if not isinstance(action, str) and issubclass(action, AzClsActionByFactory):
            try:
                json.dumps(action.kwargs)
            except Exception:
                raise TypeError('Argument action "{}#{}" kwargs cannot dump to json'.format(
                    action.import_module, action.import_name
                ))
        self.action = action

    def to_config(self, ctx):
        from azure.cli.core.translator.action import AzClsAction, AzClsActionByFactory
        key = 'action'
        if isinstance(self.action, str):
            value = self.action
        elif issubclass(self.action, AzClsAction):
            value = ctx.get_import_path(self.action.import_module, self.action.import_name)
        elif issubclass(self.action, AzClsActionByFactory):
            value = OrderedDict()
            value['factory'] = ctx.get_import_path(self.action.import_module, self.action.import_name)
            kwargs = OrderedDict()
            for k in sorted(list(self.action.kwargs.keys())):
                kwargs[k] = self.action.kwargs[k]
            value['kwargs'] = kwargs
        else:
            raise NotImplementedError()
        return key, value


class AZDevTransArgumentCompleter(AZDevTransNode):

    def __init__(self, completer):
        from azure.cli.core.translator.completer import AzCompleter, AzFuncCompleterByFactory
        if not isinstance(completer, AzCompleter):
            raise TypeError("Expect AzCompleter, got '{}'".format(completer))
        if isinstance(completer, AzFuncCompleterByFactory):
            try:
                json.dumps(completer.kwargs)
            except Exception:
                raise TypeError('Argument completer "{}" kwargs cannot dump to json'.format(completer))
        self.completer = completer

    def to_config(self, ctx):
        from azure.cli.core.translator.completer import AzFuncCompleter, AzFuncCompleterByFactory
        key = 'completer'
        if isinstance(self.completer, AzFuncCompleter):
            value = ctx.get_import_path(self.completer.import_module, self.completer.import_name)
        elif isinstance(self.completer, AzFuncCompleterByFactory):
            value = OrderedDict()
            value['factory'] = ctx.get_import_path(self.completer.import_module, self.completer.import_name)
            kwargs = OrderedDict()
            for k in sorted(list(self.completer.kwargs.keys())):
                kwargs[k] = self.completer.kwargs[k]
            value['kwargs'] = kwargs
        else:
            raise NotImplementedError()

        return key, value


class AZDevTransArgument(AZDevTransNode):
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

        self._parse_max_api(type_settings)
        self._parse_min_api(type_settings)

        if self._parse_is_ignore(type_settings):
            return

        self._parse_options_list(type_settings)
        self._parse_arg_group(type_settings)

        self._parse_action(type_settings)  # TODO:
        self._parse_choices(type_settings)
        self._parse_nargs(type_settings)

        self._parse_default(type_settings)
        self._parse_id_part(type_settings)

        self._parse_required(type_settings)
        self._parse_configured_default(type_settings)

        self._parse_const(type_settings)

        self._parse_completer(type_settings)

        self._parse_local_context_attribute(type_settings)  # TODO:
        self._parse_type(type_settings)         # TODO:
        self._parse_validator(type_settings)

        self._parse_help(type_settings)

    def _parse_deprecate_info(self, type_settings):
        deprecate_info = type_settings.get('deprecate_info', None)
        if deprecate_info is not None:
            deprecate_info = AZDevTransDeprecateInfo(deprecate_info)
        self.deprecate_info = deprecate_info

    def _parse_dest(self, type_settings):
        dest = type_settings.get('dest', None)
        assert dest == self.name

    def _parse_help(self, type_settings):
        help_description = type_settings.get('help', None)
        assert help_description is None or isinstance(help_description, str)

        help_data = {}
        if self.options_list is None:
            options = ['--{}'.format(self.name).replace('_', '-')]
        else:
            options = list(self.options_list.options.keys())
        options = set(options)
        for key, value in self.parent_command.parameters_help_data.items():
            if set(key.split()).isdisjoint(options):
                continue
            assert not help_data
            help_data = value

        self.help = AZDevTransArgumentHelp(help_description, help_data)

    def _parse_options_list(self, type_settings):
        options_list = type_settings.get('options_list', None)
        if options_list is not None and len(options_list) == 0:
            options_list = None
        if options_list is not None:
            options_list = AZDevTransArgumentOptions(options_list)
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
        # TODO: custom function signature always has default value. FYI private_link_primary in network
        # if default is not None:
        #     if self.choices is not None:
        #         if isinstance(default, list):
        #             for value in default:
        #                 assert value in self.choices
        #         else:
        #             assert default in self.choices
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
            if not isinstance(const, (str, int)):
                raise TypeError("Expect str or int, Got '{}'".format(const))
            if self.action is None or not isinstance(self.action.action, str) or 'const' not in self.action.action:
                raise TypeError("Invalid action: expect string with const")
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

    def _parse_is_ignore(self, type_settings):
        self.is_ignore = False
        if type_settings.get('action', None) == IgnoreAction and type_settings.get('help', None) == argparse.SUPPRESS:
            self.is_ignore = True
        return self.is_ignore

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

    def _parse_validator(self, type_settings):
        validator = type_settings.get('validator', None)
        if validator is not None:
            validator = AZDevTransValidator(validator)
        self.validator = validator

    def _parse_action(self, type_settings):
        # TODO: parse enum arg_type (link to SDK Model enum value)
        # TODO: parse get three state flag
        action = type_settings.get('action', None)
        if isinstance(action, str):
            action = action.strip()
            if not action:
                action = None
        if action is not None:
            action = AZDevTransArgumentAction(action)
        self.action = action

    def _parse_completer(self, type_settings):
        completer = type_settings.get('completer', None)
        if completer is not None:
            completer = AZDevTransArgumentCompleter(completer)
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
                # TODO: convert class method to string
                pass
            elif isinstance(typ, type):
                # TODO: convert class to string
                pass
            else:
                # SizeWithUnitConverter
                # TODO: convert callable instance to string
                pass
        self.typ = typ

    def to_config(self, ctx):
        key = self.name
        value = OrderedDict()
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

        if self.is_ignore:
            value['ignore'] = True
            return key, value

        if self.options_list:
            k, v = self.options_list.to_config(ctx)
            value[k] = v
        if self.help:
            k, v = self.help.to_config(ctx)
            value[k] = v

        if self.id_part:
            value['id-part'] = self.id_part
        if self.arg_group:
            value['arg-group'] = self.arg_group
        if self.nargs:
            value['nargs'] = self.nargs
        if self.required:
            value['required'] = self.required
        if self.choices:
            value['choices'] = self.choices
        if self.default:
            value['default'] = self.default
        if self.action:
            k, v = self.action.to_config(ctx)
            value[k] = v
        if self.validator:
            k, v = self.validator.to_config(ctx)
            value[k] = v
        if self.completer:
            k, v = self.completer.to_config(ctx)
            value[k] = v
        return key, value
