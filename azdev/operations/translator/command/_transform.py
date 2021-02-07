# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azdev.operations.translator.utilities import AZDevTransNode


class AZDevTransTransform(AZDevTransNode):
    key = 'transform'

    def __init__(self, transform):
        from azure.cli.core.translator.transformer import AzTransformer
        if not isinstance(transform, AzTransformer):
            raise TypeError('Transform is not an instance of "AzTransformer", get "{}"'.format(
                type(transform)))
        self.transform = transform

    def to_config(self, ctx):
        raise NotImplementedError()


class AZDevTransFuncTransform(AZDevTransTransform):

    def __init__(self, transform):
        from azure.cli.core.translator.transformer import AzFuncTransformer
        if not isinstance(transform, AzFuncTransformer):
            raise TypeError('Transform is not an instance of "AzFuncTransformer", get "{}"'.format(
                type(transform)))
        super(AZDevTransFuncTransform, self).__init__(transform)
        self.import_module = transform.import_module
        self.import_name = transform.import_name

    def to_config(self, ctx):
        value = ctx.get_import_path(self.import_module, self.import_name)
        return self.key, value


def build_command_transform(transform):
    from azure.cli.core.translator.transformer import AzTransformer, AzFuncTransformer
    if transform is None:
        return None
    if not isinstance(transform, AzTransformer):
        raise TypeError('Transform is not an instance of "AzTransformer", get "{}"'.format(
            type(transform)))

    if isinstance(transform, AzFuncTransformer):
        return AZDevTransFuncTransform(transform)
    else:
        raise NotImplementedError()
