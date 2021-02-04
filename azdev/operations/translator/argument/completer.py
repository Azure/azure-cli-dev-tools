# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections import OrderedDict
from azdev.operations.translator.utilities import AZDevTransNode, process_factory_kwargs


class AZDevTransArgumentCompleter(AZDevTransNode):
    key = 'completer'

    def __init__(self, completer):
        from azure.cli.core.translator.completer import AzCompleter
        if not isinstance(completer, AzCompleter):
            raise TypeError("Expect AzFuncCompleter, got '{}'".format(completer))
        self.completer = completer

    def to_config(self, ctx):
        raise NotImplementedError()


class AZDevTransArgumentFuncCompleter(AZDevTransArgumentCompleter):

    def __init__(self, completer):
        from azure.cli.core.translator.completer import AzFuncCompleter
        if not isinstance(completer, AzFuncCompleter):
            raise TypeError("Expect AzFuncCompleter, got '{}'".format(completer))
        super(AZDevTransArgumentFuncCompleter, self).__init__(completer)
        self.import_module = completer.import_module
        self.import_name = completer.import_name

    def to_config(self, ctx):
        value = ctx.get_import_path(self.import_module, self.import_name)
        return self.key, value


class AZDevTransArgumentFuncCompleterByFactory(AZDevTransArgumentCompleter):

    def __init__(self, completer):
        from azure.cli.core.translator.completer import AzFuncCompleterByFactory
        if not isinstance(completer, AzFuncCompleterByFactory):
            raise TypeError("Expect AzFuncCompleterByFactory, got '{}'".format(completer))
        super(AZDevTransArgumentFuncCompleterByFactory, self).__init__(completer)
        self.import_module = completer.import_module
        self.import_name = completer.import_name
        self.kwargs = process_factory_kwargs(completer.kwargs)

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
        from azure.cli.core.translator.completer import AzExternalCompleterByFactory
        if not isinstance(completer, AzExternalCompleterByFactory):
            raise TypeError("Expect AzExternalCompleterByFactory, got '{}'".format(completer))
        super(AZDevTransArgumentExternalCompleterByFactory, self).__init__(completer)
        self.import_module = completer.import_module
        self.import_name = completer.import_name
        self.kwargs = process_factory_kwargs(completer.kwargs)

    def to_config(self, ctx):
        value = OrderedDict()
        value['factory'] = ctx.get_import_path(self.import_module, self.import_name)
        kwargs = OrderedDict()
        for k in sorted(list(self.kwargs.keys())):
            kwargs[k] = self.kwargs[k]
        value['kwargs'] = kwargs
        return self.key, value


def build_argument_completer(completer):
    from azure.cli.core.translator.completer import AzCompleter, AzFuncCompleter, AzFuncCompleterByFactory, \
        AzExternalCompleterByFactory
    if completer is None:
        return None
    if not isinstance(completer, AzCompleter):
        raise TypeError("Expect AzCompleter type, got '{}'".format(completer))
    if isinstance(completer, AzFuncCompleter):
        return AZDevTransArgumentFuncCompleter(completer)
    elif isinstance(completer, AzFuncCompleterByFactory):
        return AZDevTransArgumentFuncCompleterByFactory(completer)
    elif isinstance(completer, AzExternalCompleterByFactory):
        return AZDevTransArgumentExternalCompleterByFactory(completer)
    else:
        raise NotImplementedError()
