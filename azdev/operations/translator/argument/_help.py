# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections import OrderedDict
from azdev.operations.translator.utilities import AZDevTransNode


class AZDevTransArgumentHelp(AZDevTransNode):

    def __init__(self, description, help_data):
        self.short_summary = help_data.get('short-summary', description)
        self.long_summary = help_data.get('long-summary', None)
        populator_commands = help_data.get('populator-commands', [])
        self.populator_commands = []
        if len(populator_commands) > 0:
            for command in populator_commands:
                assert isinstance(command, str)
                if command.startswith('`'):
                    command = command.strip('`')
                self.populator_commands.append(command)

    def to_config(self, ctx):
        key = 'help'
        value = OrderedDict()
        if self.short_summary:
            value['short-summary'] = self.short_summary
        if self.long_summary:
            value['long-summary'] = self.long_summary.splitlines()
        if self.populator_commands:
            value['populator-commands'] = self.populator_commands

        if set(value.keys()) == {"short-summary"}:
            value = value['short-summary']
        return key, value


def build_argument_help(help_description, help_data):
    if not help_description and not help_data:
        return None
    return AZDevTransArgumentHelp(help_description, help_data)
