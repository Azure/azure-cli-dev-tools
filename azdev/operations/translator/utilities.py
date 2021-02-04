from knack.deprecation import Deprecated
from knack.cli import CLI
from collections import OrderedDict
from six import string_types
import json
from enum import Enum
from collections.abc import KeysView, ValuesView


class _MockCliCtx:

    def __init__(self):
        self.enable_color = False

    @staticmethod
    def get_cli_version():
        from azure.cli.core import __version__
        return __version__


class ConfigurationCtx:

    def __init__(self):
        self._arg_type_reference_format_queue = []
        pass

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

    def simplify_import_path(self, path):
        # TODO: FIXME
        return path

    def get_enum_inport_path(self, module_name, name):
        # TODO: Checkout module_name
        path = name
        return path


class AZDevTransNode:

    def to_config(self, ctx):
        raise NotImplementedError()


class AZDevTransDeprecateInfo(AZDevTransNode):

    def __init__(self, table_instance):
        self.object_type = table_instance.object_type
        self.target = table_instance.target

        self.redirect = table_instance.redirect
        self.hide = table_instance.hide
        self.expiration = table_instance.expiration

        placeholder_instance = AZDevTransDeprecateInfo.get_placeholder_instance()
        self.tag_template = table_instance._get_tag(placeholder_instance)
        self.message_template = table_instance._get_message(placeholder_instance)

    def to_config(self, ctx):
        key = 'deprecate'
        value = OrderedDict()
        if self.target:
            value['target'] = self.target

        if self.redirect:
            value['redirect'] = self.redirect
        if self.hide:
            if isinstance(self.hide, bool):
                value['hide'] = self.hide
            elif isinstance(self.hide, string_types):
                value['hide-since'] = self.hide
        if self.expiration:
            value['expire-since'] = self.expiration

        if self.tag_template != self.get_default_tag_template():
            value['tag-template'] = self.tag_template
        if self.message_template != self.get_default_message_template():
            value['message-template'] = self.message_template
        return key, value

    @classmethod
    def get_placeholder_instance(cls):
        if not hasattr(cls, 'placeholder_instance'):
            placeholder_instance = Deprecated(
                cli_ctx=_MockCliCtx(),
                redirect='{redirect}',  # use {redirect} as placeholder value in template
                hide='{hide}',
                expiration='{expiration}',
                object_type='{object_type}',
                target='{target}'
            )
            setattr(cls, 'placeholder_instance', placeholder_instance)
        return getattr(cls, 'placeholder_instance')

    @classmethod
    def get_default_tag_template(cls):
        placeholder_instance = cls.get_placeholder_instance()
        return placeholder_instance._get_tag(placeholder_instance)

    @classmethod
    def get_default_message_template(cls):
        placeholder_instance = cls.get_placeholder_instance()
        return placeholder_instance._get_message(placeholder_instance)


class AZDevTransValidator(AZDevTransNode):

    def __init__(self, validator):
        from azure.cli.core.util import get_arg_list
        from azure.cli.core.translator.validator import AzValidator, AzFuncValidator, AzFuncValidatorByFactory
        if not isinstance(validator, AzValidator):
            raise TypeError('Validator is not an instance of "AzValidator", get "{}"'.format(
                type(validator)))

        if isinstance(validator, AzFuncValidator):
            arg_list = get_arg_list(validator.func)
        elif isinstance(validator, AzFuncValidatorByFactory):
            arg_list = get_arg_list(validator.instance)
        else:
            raise NotImplementedError()

        if 'ns' not in arg_list and 'cmd' not in arg_list and 'namespace' not in arg_list:
            raise TypeError('Validator "{}" signature is invalid'.format(validator))

        if isinstance(validator, AzFuncValidatorByFactory):
            try:
                json.dumps(validator.kwargs)
            except Exception:
                raise TypeError('Validator "{}#{}" kwargs cannot dump to json'.format(
                    validator.import_module, validator.import_name
                ))
        self.validator = validator

    def to_config(self, ctx):
        from azure.cli.core.translator.validator import AzFuncValidator, AzFuncValidatorByFactory
        key = 'validator'
        if isinstance(self.validator, AzFuncValidator):
            value = ctx.get_import_path(self.validator.import_module, self.validator.import_name)
        elif isinstance(self.validator, AzFuncValidatorByFactory):
            value = OrderedDict()
            value['factory'] = ctx.get_import_path(self.validator.import_module, self.validator.import_name)
            kwargs = OrderedDict()
            for k in sorted(list(self.validator.kwargs.keys())):
                kwargs[k] = self.validator.kwargs[k]
            value['kwargs'] = kwargs
        else:
            raise NotImplementedError()
        return key, value


def process_factory_kwargs(factory_kwargs, convert_cli_ctx=True, convert_enum=True):
    kwargs = {}
    for k, v in factory_kwargs.items():
        if isinstance(v, CLI) and convert_cli_ctx:
            v = '$cli_ctx'
        elif convert_enum and isinstance(v, type) and issubclass(v, Enum):
            v = {
                '_type': 'Enum',
                'module': v.__module__,
                'name': v.__name__
            }
        elif isinstance(v, KeysView):
            # TODO: Not support this. Handle TYPE_CLIENT_MAPPING to enum
            v = list(v)
        kwargs[k] = v
    try:
        json.dumps(kwargs)
    except Exception:
        raise TypeError('factory kwargs cannot dump to json')
    return kwargs
