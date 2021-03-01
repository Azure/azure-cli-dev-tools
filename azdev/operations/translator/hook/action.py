# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import argparse
import inspect
import types


class AZAction:
    pass


class AZActionClass(AZAction):
    pass


class AZActionClassByFactory(AZAction):
    pass


def action_class(action_cls):
    if not issubclass(action_cls, argparse.Action):
        raise TypeError("{} is not a subclass of argparse.Action".format(action_cls.__name__))
    name = action_cls.__name__
    bases = action_cls.__bases__
    dct = dict(action_cls.__dict__)

    dct['import_module'] = inspect.getmodule(action_cls).__name__
    dct['import_name'] = action_cls.__name__

    bases = (*bases, AZActionClass)
    return type(name, bases, dct)


def action_class_by_factory(factory):
    if not isinstance(factory, types.FunctionType):
        raise TypeError('Expect function type, Got "{}"'.format(factory))

    def wrapper(*args, **kwargs):
        sig = inspect.signature(factory)
        if len(args) > 0:
            keys = list(sig.parameters.keys())
            keys = keys[:len(args)]
            for key, value in zip(keys, args):
                kwargs[key] = value

        action_cls = factory(**kwargs)

        name = action_cls.__name__
        bases = action_cls.__bases__
        dct = dict(action_cls.__dict__)

        dct['import_module'] = inspect.getmodule(factory).__name__
        dct['import_name'] = factory.__name__
        dct['kwargs'] = kwargs

        bases = (*bases, AZActionClassByFactory)
        return type(name, bases, dct)
    return wrapper
