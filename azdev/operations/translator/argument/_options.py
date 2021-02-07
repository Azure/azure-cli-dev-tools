# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from knack.deprecation import Deprecated
from azdev.operations.translator.utilities import build_deprecate_info, AZDevTransNode
from azdev.operations.translator.utilities.deprecate_info import AZDevTransDeprecateInfo


class AZDevTransArgumentOptions(AZDevTransNode):

    def __init__(self, options_list):
        if not isinstance(options_list, (list, tuple)):
            raise TypeError('Expect list or tuple. Got "{}"'.format(type(options_list)))
        converted_options = {}
        for option in options_list:
            if not isinstance(option, str):
                if not isinstance(option, Deprecated):
                    raise TypeError('Expect Deprecated. Got "{}"'.format(type(option)))
                option = build_deprecate_info(option)
                option_str = option.target
            else:
                option_str = option
            if option_str in converted_options:
                raise TypeError('Duplicated value in options list: "{}"'.format(option_str))
            converted_options[option_str] = option
        self.options = converted_options

    def to_config(self, ctx):
        key = 'options'
        values = []
        for option_str in sorted(list(self.options.keys())):
            option = self.options[option_str]
            if isinstance(option, str):
                values.append(option)
            elif isinstance(option, AZDevTransDeprecateInfo):
                _, value = option.to_config(ctx)
                values.append(value)
        return key, values


def build_argument_options_list(options_list):
    return AZDevTransArgumentOptions(options_list)
