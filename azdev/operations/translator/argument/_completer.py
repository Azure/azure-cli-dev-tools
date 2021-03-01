# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections import OrderedDict
from azdev.operations.translator.utilities import AZDevTransNode


class AZDevTransArgumentCompleter(AZDevTransNode):
    key = 'completer'

    def __init__(self, completer):
        from azdev.operations.translator.hook.completer import AZCompleter
        if not isinstance(completer, AZCompleter):
            raise TypeError("Expect AzFuncCompleter, got '{}'".format(completer))
        self.completer = completer

    def to_config(self, ctx):
        raise NotImplementedError()


class AZDevTransArgumentFuncCompleter(AZDevTransArgumentCompleter):

    def __init__(self, completer):
        from azdev.operations.translator.hook.completer import AZCompleterFunc
        if not isinstance(completer, AZCompleterFunc):
            raise TypeError("Expect AzFuncCompleter, got '{}'".format(completer))
        super(AZDevTransArgumentFuncCompleter, self).__init__(completer)
        self.import_module = completer.import_module
        self.import_name = completer.import_name

    def to_config(self, ctx):
        value = ctx.get_import_path(self.import_module, self.import_name)
        return self.key, value


class AZDevTransArgumentFuncCompleterByFactory(AZDevTransArgumentCompleter):

    def __init__(self, completer):
        from azdev.operations.translator.hook.completer import AZCompleterByFactory
        if not isinstance(completer, AZCompleterByFactory):
            raise TypeError("Expect AzFuncCompleterByFactory, got '{}'".format(completer))
        super(AZDevTransArgumentFuncCompleterByFactory, self).__init__(completer)
        self.import_module = completer.import_module
        self.import_name = completer.import_name
        self.kwargs = self.process_factory_kwargs(completer.kwargs)

    def to_config(self, ctx):
        value = OrderedDict()
        value['factory'] = ctx.get_import_path(self.import_module, self.import_name)
        kwargs = OrderedDict()
        for k in sorted(list(self.kwargs.keys())):
            kwargs[k] = self.kwargs[k]
        value['kwargs'] = kwargs
        return self.key, value


class AZDevTransArgumentExternalCompleterByFactory(AZDevTransArgumentCompleter):

    def __init__(self, completer):
        from azdev.operations.translator.hook.completer import AZExternalCompleterByFactory
        if not isinstance(completer, AZExternalCompleterByFactory):
            raise TypeError("Expect AzExternalCompleterByFactory, got '{}'".format(completer))
        super(AZDevTransArgumentExternalCompleterByFactory, self).__init__(completer)
        self.import_module = completer.import_module
        self.import_name = completer.import_name
        self.kwargs = self.process_factory_kwargs(completer.kwargs)

    def to_config(self, ctx):
        value = OrderedDict()
        value['factory'] = ctx.get_import_path(self.import_module, self.import_name)
        kwargs = OrderedDict()
        for k in sorted(list(self.kwargs.keys())):
            kwargs[k] = self.kwargs[k]
        value['kwargs'] = kwargs
        return self.key, value


def build_argument_completer(completer):
    from azdev.operations.translator.hook.completer import AZCompleter, AZCompleterFunc, AZCompleterByFactory, \
        AZExternalCompleterByFactory
    if completer is None:
        return None
    if not isinstance(completer, AZCompleter):
        raise TypeError("Expect AzCompleter type, got '{}'".format(completer))
    if isinstance(completer, AZCompleterFunc):
        return AZDevTransArgumentFuncCompleter(completer)
    elif isinstance(completer, AZCompleterByFactory):
        return AZDevTransArgumentFuncCompleterByFactory(completer)
    elif isinstance(completer, AZExternalCompleterByFactory):
        return AZDevTransArgumentExternalCompleterByFactory(completer)
    else:
        raise NotImplementedError()
