# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import inspect
import types


class AzValidator:

    def __call__(self, cmd, namespace):
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


class AzFuncValidator(AzValidator):

    def __init__(self, func):
        if not isinstance(func, types.FunctionType):
            raise TypeError('Expect a function. Got {}'.format(type(func)))
        self.import_module = inspect.getmodule(func).__name__
        self.import_name = func.__name__
        self.func = func

    def __call__(self, cmd, namespace):
        kwargs = self._build_kwargs(self.func, cmd, namespace)
        return self.func(**kwargs)

    def __str__(self):
        return "{}#{}".format(self.import_module, self.import_name)


class AzFuncValidatorByFactory(AzValidator):

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

    def __call__(self, cmd, namespace):
        kwargs = self._build_kwargs(self.instance, cmd, namespace)
        return self.instance(**kwargs)

    def __str__(self):
        return "{}#{}".format(self.import_module, self.import_name)


def func_validator_wrapper(func):
    return AzFuncValidator(func)


def validator_factory_wrapper(factory):
    def wrapper(*args, **kwargs):
        return AzFuncValidatorByFactory(factory, args, kwargs)
    return wrapper
