# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import inspect
import types


class AZClientFactory:

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()

    def __str__(self):
        raise NotImplementedError()


class AZClientFactoryFunc(AZClientFactory):

    def __init__(self, func):
        if not isinstance(func, types.FunctionType):
            raise TypeError('Expect a function. Got {}'.format(type(func)))
        self.import_module = inspect.getmodule(func).__name__
        self.import_name = func.__name__
        self._func = func

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

    def __str__(self):
        return "{}#{}".format(self.import_module, self.import_name)


def client_factory_func(func):
    return AZClientFactoryFunc(func)