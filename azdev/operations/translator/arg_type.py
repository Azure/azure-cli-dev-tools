# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict
from azdev.operations.translator.utilities import build_deprecate_info, build_validator, AZDevTransNode


class AZDevTransArgType(AZDevTransNode):
    key = 'arg_type'

    def __init__(self, arg_type):
        from azure.cli.core.translator.arg_type import AzArgType
        if not isinstance(arg_type, AzArgType):
            raise TypeError('Expect AzArgType type, Got "{}"'.format(type(arg_type)))
        self._arg_type = arg_type

    def to_config(self, ctx):
        raise NotImplementedError()


class AZDevTransArgTypeByFactory(AZDevTransArgType):

    def __init__(self, arg_type):
        from azure.cli.core.translator.arg_type import AzArgTypeByFactory
        if not isinstance(arg_type, AzArgTypeByFactory):
            raise TypeError('Expect AzArgTypeInstance type, Got "{}"'.format(type(arg_type)))
        super(AZDevTransArgTypeByFactory, self).__init__(arg_type)
        self.import_module = arg_type.import_module
        self.import_name = arg_type.import_name
        self.kwargs = self.process_factory_kwargs(arg_type.kwargs)

    def to_config(self, ctx):
        value = OrderedDict()
        value['factory'] = ctx.get_import_path(self.import_module, self.import_name)
        kwargs = OrderedDict()
        for k in sorted(list(self.kwargs.keys())):
            v = self.kwargs[k]
            if isinstance(v, dict):
                if '_type' in v:
                    if v['_type'] == 'Enum':
                        v = ctx.get_enum_import_path(module_name=v['module'], name=v['name'])
                    else:
                        raise NotImplementedError()
            kwargs[k] = v
        value['kwargs'] = kwargs
        return self.key, value


class AZDevTransRegisteredArgType(AZDevTransArgType):

    def __init__(self, arg_type):
        from azure.cli.core.translator.arg_type import AzRegisteredArgType
        if not isinstance(arg_type, AzRegisteredArgType):
            raise TypeError('Expect AzArgTypeInstance type, Got "{}"'.format(type(arg_type)))
        super(AZDevTransRegisteredArgType, self).__init__(arg_type)
        self.register_name = arg_type.register_name

        type_settings = arg_type.settings
        self._parse_arg_type(type_settings)

        self._parse_deprecate_info(type_settings)
        self._parse_is_preview(type_settings)
        self._parse_is_experimental(type_settings)
        assert not (self.is_preview and self.is_experimental)

        self._parse_dest(type_settings)

        self._parse_max_api(type_settings)
        self._parse_min_api(type_settings)

        self._parse_options_list(type_settings)
        self._parse_arg_group(type_settings)

        self._parse_action(type_settings)
        self._parse_choices(type_settings)
        self._parse_nargs(type_settings)
        self._parse_default(type_settings)

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
        self.deprecate_info = build_deprecate_info(deprecate_info)

    def _parse_dest(self, type_settings):
        dest = type_settings.get('dest', None)
        self.dest = dest

    def _parse_help(self, type_settings):
        from azdev.operations.translator.argument import build_argument_help
        help_description = type_settings.get('help', None)
        assert help_description is None or isinstance(help_description, str)
        help_data = dict()
        self.help = build_argument_help(help_description, help_data)

    def _parse_options_list(self, type_settings):
        from azdev.operations.translator.argument import build_argument_options_list
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
        self.validator = build_validator(validator)

    def _parse_action(self, type_settings):
        from azdev.operations.translator.argument import build_argument_action
        action = type_settings.get('action', None)
        if isinstance(action, str):
            action = action.strip()
            if not action:
                action = None
        self.action = build_argument_action(action)

    def _parse_completer(self, type_settings):
        from azdev.operations.translator.argument import build_argument_completer
        completer = type_settings.get('completer', None)
        self.completer = build_argument_completer(completer)

    def _parse_local_context_attribute(self, type_settings):
        from azdev.operations.translator.argument import build_argument_local_context_attribute
        local_context_attribute = type_settings.get('local_context_attribute', None)
        self.local_context_attribute = build_argument_local_context_attribute(local_context_attribute)

    def _parse_type_converter(self, type_settings):
        from azdev.operations.translator.argument import build_argument_type_converter
        type_converter = type_settings.get('type', None)
        self.type_converter = build_argument_type_converter(type_converter)

    def _parse_arg_type(self, type_settings):
        arg_type = type_settings.get('arg_type', None)
        self.arg_type = build_arg_type(arg_type)
        if self.arg_type is not None and not isinstance(self.arg_type, AZDevTransArgTypeByFactory):
            raise TypeError("Expect AzArgTypeByFactory type, Got '{}'".format(self.arg_type))

    def to_config(self, ctx):
        reference_format = ctx.art_type_reference_format
        if reference_format:
            value = "${}".format(self.register_name)
            return self.key, value

        value = OrderedDict()
        if self.dest:
            value['dest'] = self.dest

        if self.arg_type:
            if not isinstance(self.arg_type, AZDevTransArgTypeByFactory):
                raise TypeError("Expect AzArgTypeByFactory type, Got '{}'".format(self.arg_type))
            ctx.set_art_type_reference_format(False)
            k, v = self.arg_type.to_config(ctx)
            value[k] = v
            ctx.unset_art_type_reference_format()

        if self.deprecate_info:
            k, v = self.deprecate_info.to_config(ctx)
            value[k] = v
        if self.is_preview:
            k = 'preview'
            v = self.is_preview
            value[k] = v
        if self.is_experimental:
            k = 'experimental'
            v = self.is_experimental
            value[k] = v
        if self.min_api:
            k = 'min-api'
            v = self.min_api
            value[k] = v
        if self.max_api:
            k = 'max-api'
            v = self.max_api
            value[k] = v

        if self.options_list:
            k, v = self.options_list.to_config(ctx)
            value[k] = v
        if self.help:
            k, v = self.help.to_config(ctx)
            value[k] = v

        if self.id_part:
            k = 'id-part'
            v = self.id_part
            value[k] = v
        if self.arg_group:
            k = 'arg-group'
            v = self.arg_group
            value[k] = v
        if self.nargs:
            k = 'nargs'
            v = self.nargs
            value[k] = v
        if self.required:
            k = 'required'
            v = self.required
            value[k] = v
        if self.choices:
            k = 'choices'
            v = self.choices
            value[k] = v
        if self.default:
            k = 'default'
            v = self.default
            value[k] = v
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

        return self.register_name, value


def build_arg_type(arg_type):
    from azure.cli.core.translator.arg_type import AzArgType, AzRegisteredArgType, AzArgTypeByFactory
    if arg_type is None:
        return None

    if not isinstance(arg_type, AzArgType):
        raise TypeError("Expect str or AzArgType type, got '{}'".format(arg_type))
    if isinstance(arg_type, AzRegisteredArgType):
        return AZDevTransRegisteredArgType(arg_type)
    elif isinstance(arg_type, AzArgTypeByFactory):
        return AZDevTransArgTypeByFactory(arg_type)
    else:
        raise NotImplementedError()

