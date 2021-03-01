# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import inspect
import types
from knack.arguments import CLIArgumentType


class AZArgType(CLIArgumentType):

    def __init__(self, overrides=None, **kwargs):
        self._is_registered = False
        super(AZArgType, self).__init__(overrides=overrides, **kwargs)
        self._is_registered = True

    def update(self, *args, **kwargs):
        if self._is_registered:
            raise NotImplementedError("Not support to update registered arg type")
        super(AZArgType, self).update(*args, **kwargs)


class AZRegisteredArgType(AZArgType):

    def __init__(self, register_name, import_module, overrides=None, **kwargs):
        self.import_module = import_module
        self.register_name = register_name
        # if not isinstance(instance, CLIArgumentType):
        #     raise TypeError('Expect type is CLIArgumentType. Got "{}"'.format(type(instance)))
        super(AZRegisteredArgType, self).__init__(overrides=overrides, **kwargs)


class AZArgTypeByFactory(AZArgType):

    def __init__(self, instance, factory, args, kwargs):
        if isinstance(factory, types.FunctionType):  # support a factory function which return value is callable
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
        if not isinstance(instance, CLIArgumentType):
            raise TypeError('Expect type is CLIArgumentType. Got "{}"'.format(type(instance)))
        super(AZArgTypeByFactory, self).__init__(**instance.settings)


def register_arg_type(register_name, overrides=None, **kwargs):
    parent_frame = inspect.stack()[1].frame
    import_module = inspect.getmodule(parent_frame).__name__
    return AZRegisteredArgType(register_name, import_module, overrides=overrides, **kwargs)


def arg_type_by_factory(factory):
    def wrapper(*args, **kwargs):
        instance = factory(*args, **kwargs)
        if instance is None:
            return None
        else:
            return AZArgTypeByFactory(instance, factory, args, kwargs)
    return wrapper
