# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections import OrderedDict
from azdev.operations.translator.utilities import AZDevTransNode


class AZDevTransArgumentTypeConverter(AZDevTransNode):
    key = 'type'

    def __init__(self, converter):
        self.converter = converter

    def to_config(self, ctx):
        raise NotImplementedError()


class AZDevTransArgumentTypeConverterBuildIn(AZDevTransArgumentTypeConverter):

    def __init__(self, converter):
        if converter not in (str, int, float, bool):
            raise TypeError('Expect str, int, float or bool, Got "{}"'.format(converter))
        super(AZDevTransArgumentTypeConverterBuildIn, self).__init__(converter)

    def to_config(self, ctx):
        value = str(self.converter)
        return self.key, value


class AZDevTransArgumentTypeConverterFunc(AZDevTransArgumentTypeConverter):

    def __init__(self, converter):
        from azdev.operations.translator.hook.type_converter import AZTypeConverterFunc
        if not isinstance(converter, AZTypeConverterFunc):
            raise TypeError('Expect AzFuncTypeConverter, Got "{}"'.format(converter))
        super(AZDevTransArgumentTypeConverterFunc, self).__init__(converter)
        self.import_module = converter.import_module
        self.import_name = converter.import_name

    def to_config(self, ctx):
        value = ctx.get_import_path(self.import_module, self.import_name)
        return self.key, value


class AZDevTransArgumentTypeConverterByFactory(AZDevTransArgumentTypeConverter):

    def __init__(self, converter):
        from azdev.operations.translator.hook.type_converter import AZTypeConverterByFactory
        if not isinstance(converter, AZTypeConverterByFactory):
            raise TypeError('Expect AzFuncTypeConverterByFactory, Got "{}"'.format(converter))
        super(AZDevTransArgumentTypeConverterByFactory, self).__init__(converter)
        self.import_module = converter.import_module
        self.import_name = converter.import_name
        self.kwargs = self.process_factory_kwargs(converter.kwargs)

    def to_config(self, ctx):
        value = OrderedDict()
        value['factory'] = ctx.get_import_path(self.import_module, self.import_name)
        kwargs = OrderedDict()
        for k in sorted(list(self.kwargs.keys())):
            kwargs[k] = self.kwargs[k]
        value['kwargs'] = kwargs
        return self.key, value


def build_argument_type_converter(converter):
    from azdev.operations.translator.hook.type_converter import AZTypeConverterFunc, AZTypeConverterByFactory
    if converter is None:
        return None
    if converter in (str, int, float, bool):
        return AZDevTransArgumentTypeConverterBuildIn(converter)
    elif isinstance(converter, AZTypeConverterFunc):
        return AZDevTransArgumentTypeConverterFunc(converter)
    elif isinstance(converter, AZTypeConverterByFactory):
        return AZDevTransArgumentTypeConverterByFactory(converter)

