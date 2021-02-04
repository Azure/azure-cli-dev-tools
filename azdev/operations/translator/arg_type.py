# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .utilities import AZDevTransNode, process_factory_kwargs
from collections import OrderedDict


class AZDevTransArgType(AZDevTransNode):
    key = 'arg_type'

    def __init__(self, arg_type):
        from azure.cli.core.translator.arg_type import AzArgType
        if not isinstance(arg_type, AzArgType):
            raise TypeError('Expect AzArgType type, Got "{}"'.format(type(arg_type)))
        self.arg_type = arg_type

    def to_config(self, ctx):
        raise NotImplementedError()


class AZDevTransArgTypeByFactory(AZDevTransArgType):

    def __init__(self, arg_type):
        from azure.cli.core.translator.arg_type import AzArgTypeByFactory
        if not isinstance(arg_type, AzArgTypeByFactory):
            raise TypeError('Expect AzArgTypeInstance type, Got "{}"'.format(type(arg_type)))
        super(AZDevTransArgTypeByFactory, self).__init__(arg_type)
        self.import_module = arg_type.import_module
        self.import_name = arg_type.import_name
        self.kwargs = process_factory_kwargs(arg_type.kwargs)

    def to_config(self, ctx):
        value = OrderedDict()
        value['factory'] = ctx.get_import_path(self.import_module, self.import_name)
        kwargs = OrderedDict()
        for k in sorted(list(self.kwargs.keys())):
            kwargs[k] = self.kwargs[k]
        value['kwargs'] = kwargs
        return self.key, value


class AZDevTransArgTypeInstance(AZDevTransArgType):

    def __init__(self, arg_type):
        from azure.cli.core.translator.arg_type import AzArgTypeInstance
        if not isinstance(arg_type, AzArgTypeInstance):
            raise TypeError('Expect AzArgTypeInstance type, Got "{}"'.format(type(arg_type)))
        super(AZDevTransArgTypeInstance, self).__init__(arg_type)

    def to_config(self, ctx):
        # TODO:
        return self.key, None




