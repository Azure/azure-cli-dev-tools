from knack.deprecation import Deprecated


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
