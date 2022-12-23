# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import types
import inspect


class AzTransformer:

    def __call__(self, result):
        raise NotImplementedError()

    def __str__(self):
        raise NotImplementedError()


class AzFuncTransformer(AzTransformer):

    def __init__(self, func):
        if not isinstance(func, types.FunctionType):
            raise TypeError('Expect a function. Got {}'.format(type(func)))
        self.import_module = inspect.getmodule(func).__name__
        self.import_name = func.__name__
        self.func = func

    def __call__(self, result):
        return self.func(result)

    def __str__(self):
        return "{}#{}".format(self.import_module, self.import_name)


def func_transformer_wrapper(func):
    return AzFuncTransformer(func)
