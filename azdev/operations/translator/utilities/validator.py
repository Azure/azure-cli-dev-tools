# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections import OrderedDict
from .trans_node import AZDevTransNode


class AZDevTransValidator(AZDevTransNode):
    key = 'validator'

    def __init__(self, validator, arg_list):
        if 'ns' not in arg_list and 'cmd' not in arg_list and 'namespace' not in arg_list:
            raise TypeError('Validator "{}" signature is invalid'.format(validator))
        self.validator = validator

    def to_config(self, ctx):
        raise NotImplementedError()


class AZDevTransFuncValidator(AZDevTransValidator):

    def __init__(self, validator):
        from azure.cli.core.util import get_arg_list
        from azdev.operations.translator.hook.validator import AZValidatorFunc
        if not isinstance(validator, AZValidatorFunc):
            raise TypeError('Validator is not an instance of "AzValidator", get "{}"'.format(
                type(validator)))
        arg_list = get_arg_list(validator.func)
        super(AZDevTransFuncValidator, self).__init__(validator, arg_list)
        self.import_module = validator.import_module
        self.import_name = validator.import_name

    def to_config(self, ctx):
        value = ctx.get_import_path(self.import_module, self.import_name)
        return self.key, value


class AZDevTransFuncValidatorByFactory(AZDevTransValidator):

    def __init__(self, validator):
        from azure.cli.core.util import get_arg_list
        from azdev.operations.translator.hook.validator import AZValidatorByFactory
        if not isinstance(validator, AZValidatorByFactory):
            raise TypeError('Validator is not an instance of "AzFuncValidatorByFactory", get "{}"'.format(
                type(validator)))
        arg_list = get_arg_list(validator.instance)
        super(AZDevTransFuncValidatorByFactory, self).__init__(validator, arg_list)
        self.import_module = validator.import_module
        self.import_name = validator.import_name
        self.kwargs = self.process_factory_kwargs(validator.kwargs)

    def to_config(self, ctx):
        value = OrderedDict()
        value['factory'] = ctx.get_import_path(self.import_module, self.import_name)
        kwargs = OrderedDict()
        for k in sorted(list(self.kwargs.keys())):
            kwargs[k] = self.kwargs[k]
        value['kwargs'] = kwargs
        return self.key, value


def build_validator(validator):
    if validator is None:
        return None
    from azdev.operations.translator.hook.validator import AZValidator, AZValidatorFunc, AZValidatorByFactory
    if not isinstance(validator, AZValidator):
        raise TypeError('Validator is not an instance of "AzValidator", get "{}"'.format(
            type(validator)))

    if isinstance(validator, AZValidatorFunc):
        return AZDevTransFuncValidator(validator)
    elif isinstance(validator, AZValidatorByFactory):
        return AZDevTransFuncValidatorByFactory(validator)
    else:
        raise NotImplementedError()

