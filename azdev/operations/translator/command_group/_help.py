# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azdev.operations.translator.utilities import AZDevTransNode
from collections import OrderedDict


class AZDevTransCommandGroupHelp(AZDevTransNode):

    def __init__(self, help_data):
        assert help_data['type'].lower() == 'group'
        self.short_summary = help_data.get('short-summary', None)
        self.long_summary = help_data.get('long-summary', None)
        assert self.short_summary

    def to_config(self, ctx):
        key = 'help'
        value = OrderedDict()
        if self.short_summary:
            value['short-summary'] = self.short_summary
        if self.long_summary:
            value['long-summary'] = self.long_summary.splitlines()

        if set(value.keys()) == {"short-summary"}:
            value = value['short-summary']
        return key, value


def build_command_group_help(help_data):
    return AZDevTransCommandGroupHelp(help_data)
