from knack.arguments import IgnoreAction
from collections import OrderedDict
from azdev.operations.translator.utilities import AZDevTransDeprecateInfo, AZDevTransValidator, AZDevTransNode
import argparse
from azdev.operations.translator.arg_type import build_arg_type
from .help import build_argument_help
from .options import build_argument_options_list
from .action import build_argument_action
from .completer import build_argument_completer
from .type_converter import build_argument_type_converter
from .local_context_attribute import build_argument_local_context_attribute


class AZDevTransArgument(AZDevTransNode):
    # supported: 'deprecate_info', 'is_preview', 'is_experimental', 'dest', 'help', 'options_list', 'action', 'arg_group', 'arg_type', 'choices', 'default', 'completer', 'configured_default', 'const', 'id_part', 'local_context_attribute', 'max_api', 'min_api', 'nargs',  'required', 'type', 'validator'
    # ignored: 'metavar', 'operation_group', 'resource_type', 'dest'
    # invalid: 'option_list', 'metave', ' FilesCompleter'
    # TODO CHECK: option_strings, default_value_source, custom_command_type, command_type

    def __init__(self, name, parent_command, table_instance):
        self.name = name
        self.parent_command = parent_command

        type_settings = table_instance.type.settings
        if 'arg_type' in type_settings:
            # Block storage has_header arg_type: https://github.com/Azure/azure-cli/blob/dd891a940b3a15751ecfbf71b62a1aafb1cfe608/src/azure-cli/azure/cli/command_modules/storage/_params.py#L887
            raise TypeError("Not support nested arg_type")

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

        self._parse_action(type_settings)
        self._parse_choices(type_settings)
        self._parse_nargs(type_settings)
        self._parse_default(type_settings)
        self._parse_arg_type(type_settings)

        self._parse_id_part(type_settings)
        self._parse_required(type_settings)
        self._parse_configured_default(type_settings)

        self._parse_const(type_settings)
        self._parse_completer(type_settings)

        self._parse_local_context_attribute(type_settings)
        self._parse_type_converter(type_settings)
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

        self.help = build_argument_help(help_description, help_data)

    def _parse_options_list(self, type_settings):
        options_list = type_settings.get('options_list', None)
        if options_list is not None and len(options_list) == 0:
            options_list = None
        if options_list is not None:
            options_list = build_argument_options_list(options_list)
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
        self.action = build_argument_action(action)

    def _parse_completer(self, type_settings):
        completer = type_settings.get('completer', None)
        self.completer = build_argument_completer(completer)

    def _parse_local_context_attribute(self, type_settings):
        local_context_attribute = type_settings.get('local_context_attribute', None)
        self.local_context_attribute = build_argument_local_context_attribute(local_context_attribute)

    def _parse_type_converter(self, type_settings):
        type_converter = type_settings.get('type', None)
        self.type_converter = build_argument_type_converter(type_converter)

    def _parse_arg_type(self, type_settings):
        arg_type = type_settings.get('_arg_type', None)
        self.arg_type = build_arg_type(arg_type)

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
        if self.local_context_attribute:
            k, v = self.local_context_attribute.to_config(ctx)
            value[k] = v
        if self.type_converter:
            k, v = self.type_converter.to_config(ctx)
            value[k] = v
        return key, value
