# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azdev.operations.translator.utilities import AZDevTransNode


class AZDevTransTableTransformer(AZDevTransNode):
    key = 'table-transformer'

    def __init__(self, table_transformer):
        from azdev.operations.translator.hook.transformer import AZTransformer
        if not isinstance(table_transformer, str) and not isinstance(table_transformer, AZTransformer):
            raise TypeError('Table transform is not a string or an instance of "AzTransformer", get "{}"'.format(
                type(table_transformer)))
        self.table_transformer = table_transformer

    def to_config(self, ctx):
        raise NotImplementedError()


class AZDevTransStrTableTransformer(AZDevTransTableTransformer):

    def __init__(self, table_transformer):
        from azdev.operations.translator.hook.transformer import AZTransformerFunc
        if not isinstance(table_transformer, str) and not isinstance(table_transformer, AZTransformerFunc):
            raise TypeError('Table transform is not a string, get "{}"'.format(
                type(table_transformer)))
        super(AZDevTransStrTableTransformer, self).__init__(table_transformer)
        self.retrieve_data = table_transformer

    def to_config(self, ctx):
        # TODO: distinguish string and AzFuncTransformer value
        value = self.retrieve_data
        return self.key, value


class AZDevTransFuncTableTransformer(AZDevTransTableTransformer):

    def __init__(self, table_transformer):
        from azdev.operations.translator.hook.transformer import AZTransformerFunc
        if not isinstance(table_transformer, AZTransformerFunc):
            raise TypeError('Table transform is not an instance of "AzFuncTransformer", get "{}"'.format(
                type(table_transformer)))
        super(AZDevTransFuncTableTransformer, self).__init__(table_transformer)
        self.import_module = table_transformer.import_module
        self.import_name = table_transformer.import_name

    def to_config(self, ctx):
        value = ctx.get_import_path(self.import_module, self.import_name)
        return self.key, value


def build_command_table_transformer(table_transformer):
    from azdev.operations.translator.hook.transformer import AZTransformer, AZTransformerFunc
    if isinstance(table_transformer, str):
        table_transformer = table_transformer.strip()
        if not table_transformer:
            table_transformer = None
    if table_transformer is None:
        return None
    if not isinstance(table_transformer, str) and not isinstance(table_transformer, AZTransformer):
        raise TypeError('Table transform is not a string or an instance of "AzTransformer", get "{}"'.format(
            type(table_transformer)))
    if isinstance(table_transformer, str):
        return AZDevTransStrTableTransformer(table_transformer)
    elif isinstance(table_transformer, AZTransformerFunc):
        return AZDevTransFuncTableTransformer(table_transformer)
    else:
        raise NotImplementedError()
