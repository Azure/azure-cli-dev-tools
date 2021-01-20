from knack.deprecation import Deprecated


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
