# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azdev.operations.translator.utilities import AZDevTransNode


class AZDevTransClientFactory(AZDevTransNode):
    key = "client-factory"

    def __init__(self, client_factory):
        from azure.cli.core.translator.client_factory import AzClientFactory
        if not isinstance(client_factory, AzClientFactory):
            raise TypeError('Client factory is not an instance of "AzClientFactory", get "{}"'.format(
                type(client_factory)))
        self.client_factory = client_factory

    def to_config(self, ctx):
        raise NotImplementedError()


class AZDevTransFuncClientFactory(AZDevTransClientFactory):

    def __init__(self, client_factory):
        from azure.cli.core.translator.client_factory import AzFuncClientFactory
        if not isinstance(client_factory, AzFuncClientFactory):
            raise TypeError('Client factory is not an instance of "AzFuncClientFactory", get "{}"'.format(
                type(client_factory)))
        super(AZDevTransFuncClientFactory, self).__init__(client_factory)
        self.import_module = client_factory.import_module
        self.import_name = client_factory.import_name

    def to_config(self, ctx):
        value = ctx.get_import_path(self.import_module, self.import_name)
        return self.key, value


def build_client_factory(client_factory):
    from azure.cli.core.translator.client_factory import AzClientFactory, AzFuncClientFactory
    if client_factory is None:
        return None
    if not isinstance(client_factory, AzClientFactory):
        raise TypeError('Client factory is not an instance of "AzClientFactory", get "{}"'.format(
            type(client_factory)))
    if isinstance(client_factory, AzFuncClientFactory):
        return AZDevTransFuncClientFactory(client_factory)
    else:
        raise NotImplementedError()
