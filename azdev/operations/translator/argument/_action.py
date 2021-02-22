# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections import OrderedDict
from azdev.operations.translator.utilities import AZDevTransNode


class AZDevTransArgumentAction(AZDevTransNode):

    key = 'action'

    def __init__(self, action):
        from azdev.operations.translator.hook.action import AzAction
        if not isinstance(action, str) and not issubclass(action, AzAction):
            raise TypeError("Expect str or AzAction type, got '{}'".format(action))
        self.action = action

    def to_config(self, ctx):
        raise NotImplementedError()


class AZDevTransArgumentActionByStr(AZDevTransArgumentAction):

    def __init__(self, action):
        if not isinstance(action, str):
            raise TypeError("Expect str or AzAction type, got '{}'".format(action))
        super(AZDevTransArgumentActionByStr, self).__init__(action)

    def to_config(self, ctx):
        value = self.action
        return self.key, value


class AZDevTransArgumentClsAction(AZDevTransArgumentAction):

    def __init__(self, action):
        from azdev.operations.translator.hook.action import AzClsAction
        if not issubclass(action, AzClsAction):
            raise TypeError("Expect str or AzClsAction type, got '{}'".format(action))
        super(AZDevTransArgumentClsAction, self).__init__(action)
        self.import_module = action.import_module
        self.import_name = action.import_name

    def to_config(self, ctx):
        value = ctx.get_import_path(self.import_module, self.import_name)
        return self.key, value


class AZDevTransArgumentClsActionByFactory(AZDevTransArgumentAction):

    def __init__(self, action):
        from azdev.operations.translator.hook.action import AzClsActionByFactory
        if not issubclass(action, AzClsActionByFactory):
            raise TypeError("Expect str or AzClsActionByFactory type, got '{}'".format(action))
        super(AZDevTransArgumentClsActionByFactory, self).__init__(action)
        self.import_module = action.import_module
        self.import_name = action.import_name
        self.kwargs = self.process_factory_kwargs(action.kwargs)

    def to_config(self, ctx):
        value = OrderedDict()
        value['factory'] = ctx.get_import_path(self.import_module, self.import_name)
        kwargs = OrderedDict()
        for k in sorted(list(self.kwargs.keys())):
            kwargs[k] = self.kwargs[k]
        value['kwargs'] = kwargs
        return self.key, value


def build_argument_action(action):
    from azdev.operations.translator.hook.action import AzAction, AzClsAction, AzClsActionByFactory
    if action is None:
        return None

    if isinstance(action, str):
        return AZDevTransArgumentActionByStr(action)
    elif not isinstance(action, type) or not issubclass(action, AzAction):
        raise TypeError("Expect str or AzAction type, got '{}'".format(action))
    elif issubclass(action, AzClsAction):
        return AZDevTransArgumentClsAction(action)
    elif issubclass(action, AzClsActionByFactory):
        return AZDevTransArgumentClsActionByFactory(action)
    else:
        raise NotImplementedError()
