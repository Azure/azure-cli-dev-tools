from knack.deprecation import Deprecated
from collections import OrderedDict
from six import string_types
import json


class _MockCliCtx:

    def __init__(self):
        self.enable_color = False

    @staticmethod
    def get_cli_version():
        from azure.cli.core import __version__
        return __version__


class ConfigurationCtx:

    def __init__(self):
        pass

    def get_import_path(self, module_name, name):
        path = "{}#{}".format(module_name, name)
        return self.simplify_import_path(path)

    def simplify_import_path(self, path):
        # TODO: FIXME
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
        from azure.cli.core.translator.validator import AzValidator, AzFuncValidator, AzClassValidator
        if not isinstance(validator, AzValidator):
            raise TypeError('Validator is not an instance of "AzValidator", get "{}"'.format(
                type(validator)))

        if isinstance(validator, AzFuncValidator):
            arg_list = get_arg_list(validator.func)
        elif isinstance(validator, AzClassValidator):
            arg_list = get_arg_list(validator.instance)
        else:
            raise NotImplementedError()

        if 'ns' not in arg_list and 'cmd' not in arg_list and 'namespace' not in arg_list:
            raise TypeError('Validator "{}" signature is invalid'.format(validator))

        if isinstance(validator, AzClassValidator):
            try:
                json.dumps(validator.kwargs)
            except Exception:
                raise TypeError('Validator "{}#{}" kwargs cannot dump to json'.format(
                    validator.module_name, validator.name
                ))
        self.validator = validator

    def to_config(self, ctx):
        from azure.cli.core.translator.validator import AzValidator, AzFuncValidator, AzClassValidator
        key = 'validator'
        if isinstance(self.validator, AzFuncValidator):
            value = ctx.get_import_path(self.validator.module_name, self.validator.name)
        elif isinstance(self.validator, AzClassValidator):
            value = OrderedDict()
            value['cls'] = ctx.get_import_path(self.validator.module_name, self.validator.name)
            kwargs = OrderedDict()
            for k in sorted(list(self.validator.kwargs.keys())):
                kwargs[k] = self.validator.kwargs[k]
            value['kwargs'] = kwargs
        else:
            raise NotImplementedError()
        return key, value

