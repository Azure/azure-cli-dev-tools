# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.deprecation import Deprecated
from collections import OrderedDict
from six import string_types
from .trans_node import AZDevTransNode


class _MockCliCtx:

    def __init__(self):
        self.enable_color = False

    @staticmethod
    def get_cli_version():
        from azure.cli.core import __version__
        return __version__


class AZDevTransDeprecateInfo(AZDevTransNode):

    _placeholder_instance = Deprecated(
        cli_ctx=_MockCliCtx(),
        redirect='{redirect}',  # use {redirect} as placeholder value in template
        hide='{hide}',
        expiration='{expiration}',
        object_type='{object_type}',
        target='{target}'
    )

    _default_tag_template = _placeholder_instance._get_tag(_placeholder_instance)

    _default_message_template = _placeholder_instance._get_message(_placeholder_instance)

    def __init__(self, table_instance):
        self.object_type = table_instance.object_type
        self.target = table_instance.target

        self.redirect = table_instance.redirect
        self.hide = table_instance.hide
        self.expiration = table_instance.expiration

        self.tag_template = table_instance._get_tag(self._placeholder_instance)
        self.message_template = table_instance._get_message(self._placeholder_instance)

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

        if self.tag_template != self._default_tag_template:
            value['tag-template'] = self.tag_template
        if self.message_template != self._default_message_template:
            value['message-template'] = self.message_template
        return key, value


def build_deprecate_info(deprecate_info):
    if deprecate_info is None:
        return None
    return AZDevTransDeprecateInfo(deprecate_info)
