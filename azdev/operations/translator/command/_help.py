# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections import OrderedDict
from azdev.operations.translator.utilities import AZDevTransNode


class AZDevTransCommandHelp(AZDevTransNode):

    def __init__(self, description, help_data):
        self.short_summary = None
        self.long_summary = None

        try:
            self.short_summary = description[:description.index('.')]
            long_summary = description[description.index('.') + 1:].lstrip()
            self.long_summary = ' '.join(long_summary.splitlines())
        except (ValueError, AttributeError):
            self.short_summary = description

        if help_data:
            if help_data['type'].lower() != 'command':
                raise TypeError('help type is not equal to "command"')
            short_summary = help_data.get('short-summary', None)
            long_summary = help_data.get('long-summary', None)
            if short_summary:
                self.short_summary = short_summary
            if long_summary:
                self.long_summary = long_summary
        if not self.short_summary:
            raise TypeError("Short summary of command help is empty")

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


def build_command_help(help_description, help_data):
    if not help_description and not help_data:
        return None
    return AZDevTransCommandHelp(help_description, help_data)
