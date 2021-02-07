# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections import OrderedDict
from azdev.operations.translator.utilities import AZDevTransNode


class AZDevTransArgumentLocalContextAttribute(AZDevTransNode):
    key = 'local-context-attribute'

    def __init__(self, attribute):
        from azure.cli.core.local_context import LocalContextAttribute, LocalContextAction
        if not isinstance(attribute, LocalContextAttribute):
            raise TypeError("Expect LocalContextAttribute, got '{}'".format(attribute))
        self.attribute = attribute

        self.name = attribute.name
        actions = []
        if attribute.actions:
            for action in attribute.actions:
                if not isinstance(action, LocalContextAction):
                    raise TypeError('Expect LocalContextAction type, Got "{}"'.format(action))
                actions.append(str(action))
        self.actions = actions
        scopes = []
        if attribute.scopes:
            for scope in attribute.scopes:
                if not isinstance(scope, str):
                    raise TypeError('Expect str type, Got "{}"'.format(scope))
                scopes.append(scope)
        self.scopes = scopes

    def to_config(self, ctx):
        value = OrderedDict()
        value['name'] = self.name
        if self.actions:
            value['actions'] = self.actions
        if self.scopes:
            value['scopes'] = self.scopes
        return self.key, value


def build_argument_local_context_attribute(attribute):
    from azure.cli.core.local_context import LocalContextAttribute
    if attribute is None:
        return None
    if isinstance(attribute, LocalContextAttribute):
        return AZDevTransArgumentLocalContextAttribute(attribute)
    else:
        raise NotImplementedError()
