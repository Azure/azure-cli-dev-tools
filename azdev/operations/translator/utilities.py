from knack.deprecation import Deprecated
from azure.cli.core.translator.validator import AzValidator, AzFuncValidator, AzClassValidator
from azure.cli.core.util import get_arg_list


class _MockCliCtx:

    def __init__(self):
        self.enable_color = False

    @staticmethod
    def get_cli_version():
        from azure.cli.core import __version__
        return __version__


class AZDevTransDeprecateInfo:

    def __init__(self, table_instance):
        self.object_type = table_instance.object_type
        self.target = table_instance.target

        self.redirect = table_instance.redirect
        self.hide = table_instance.hide
        self.expiration = table_instance.expiration

        placeholder_instance = AZDevTransDeprecateInfo.get_placeholder_instance()
        self.tag_template = table_instance._get_tag(placeholder_instance)
        self.message_template = table_instance._get_message(placeholder_instance)

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


def check_validator(validator):
    if validator is not None:
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
