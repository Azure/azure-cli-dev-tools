# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections import OrderedDict
from azdev.operations.translator.utilities import AZDevTransNode


class AZDevTransArgumentLocalContextAttribute(AZDevTransNode):
    key = 'local-context-attribute'

    def __init__(self, attribute):
        from azure.cli.core.local_context import LocalContextAttribute
        if not isinstance(attribute, LocalContextAttribute):
            raise TypeError("Expect LocalContextAttribute, got '{}'".format(attribute))
        self.attribute = attribute

    def to_config(self, ctx):
        value = OrderedDict()
        value['name'] = self.attribute.name
        value['actions'] = self.attribute.actions
        value['scopes'] = self.attribute.scopes
        return self.key, value


def build_argument_local_context_attribute(attribute):
    from azure.cli.core.local_context import LocalContextAttribute
    if attribute is None:
        return None
    if isinstance(attribute, LocalContextAttribute):
        return AZDevTransArgumentLocalContextAttribute(attribute)
    else:
        return NotImplementedError()
