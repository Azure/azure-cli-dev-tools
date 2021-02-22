# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import inspect
import types


class AzCompleter:

    def __call__(self, **kwargs):
        raise NotImplementedError()

    def __str__(self):
        raise NotImplementedError()

    @staticmethod
    def _build_kwargs(func, cmd, namespace):  # pylint: disable=no-self-use
        from azure.cli.core.util import get_arg_list
        arg_list = get_arg_list(func)
        kwargs = {}
        if 'cmd' in arg_list:
            kwargs['cmd'] = cmd  # pylint: disable=protected-access
        if 'namespace' in arg_list:
            kwargs['namespace'] = namespace
        if 'ns' in arg_list:
            kwargs['ns'] = namespace
        return kwargs


class AzFuncCompleter(AzCompleter):

    def __init__(self, func):
        if not isinstance(func, types.FunctionType):
            raise TypeError('Expect a function. Got {}'.format(type(func)))
        self.import_module = inspect.getmodule(func).__name__
        self.import_name = func.__name__
        self.func = func

    def __call__(self, **kwargs):
        namespace = kwargs['parsed_args']
        prefix = kwargs['prefix']
        cmd = namespace._cmd  # pylint: disable=protected-access
        return self.func(cmd, prefix, namespace)

    def __str__(self):
        return "{}#{}".format(self.import_module, self.import_name)


class AzFuncCompleterByFactory(AzCompleter):

    def __init__(self, factory, args, kwargs):
        if isinstance(factory, types.FunctionType):     # support a factory function which return value is callable
            sig = inspect.signature(factory)
        elif isinstance(factory, type):
            sig = inspect.signature(factory.__init__)
        else:
            raise TypeError("Expect a function or a class. Got {}".format(type(factory)))

        self.import_module = inspect.getmodule(factory).__name__
        self.import_name = factory.__name__
        self.kwargs = {}
        if len(args) > 0:
            keys = list(sig.parameters.keys())
            if keys[0] == 'self':
                keys = keys[1:]
            keys = keys[:len(args)]
            for key, value in zip(keys, args):
                self.kwargs[key] = value
        self.kwargs.update(kwargs)
        self.instance = factory(*args, **kwargs)
        if not callable(self.instance):
            raise TypeError('Expect a callable instance.')

    def __call__(self, **kwargs):
        namespace = kwargs['parsed_args']
        prefix = kwargs['prefix']
        cmd = namespace._cmd  # pylint: disable=protected-access
        return self.instance(cmd, prefix, namespace)

    def __str__(self):
        return "{}#{}".format(self.import_module, self.import_name)


class AzExternalCompleterByFactory(AzCompleter):

    def __init__(self, factory, args, kwargs):
        from azure.cli.core.translator import external_completer
        if isinstance(factory, types.FunctionType):  # support a factory function which return value is callable
            sig = inspect.signature(factory)
        elif isinstance(factory, type):
            sig = inspect.signature(factory.__init__)
        else:
            raise TypeError("Expect a function or a class. Got {}".format(type(factory)))

        self.import_module = external_completer.__name__
        self.import_name = factory.__name__
        self.kwargs = {}
        if len(args) > 0:
            keys = list(sig.parameters.keys())
            if keys[0] == 'self':
                keys = keys[1:]
            keys = keys[:len(args)]
            for key, value in zip(keys, args):
                self.kwargs[key] = value
        self.kwargs.update(kwargs)
        self.instance = factory(*args, **kwargs)
        if not callable(self.instance):
            raise TypeError('Expect a callable instance.')

    def __call__(self, *args, **kwargs):
        return self.instance(*args, **kwargs)

    def __str__(self):
        return "{}#{}".format(self.import_module, self.import_name)


def func_completer_wrapper(func):
    return AzFuncCompleter(func)


def completer_factory_wrapper(factory):
    def wrapper(*args, **kwargs):
        return AzFuncCompleterByFactory(factory, args, kwargs)
    return wrapper


def build_external_completer_instance(cls, args, kwargs):
    return AzExternalCompleterByFactory(cls, args, kwargs)
