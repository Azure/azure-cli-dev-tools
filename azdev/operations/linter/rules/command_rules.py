# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from ..rule_decorators import CommandRule
from ..linter import RuleError, LinterSeverity


@CommandRule(LinterSeverity.HIGH)
def missing_command_help(linter, command_name):
    if not linter.get_command_help(command_name) and not linter.command_expired(command_name):
        raise RuleError('Missing help')


@CommandRule(LinterSeverity.HIGH)
def no_ids_for_list_commands(linter, command_name):
    if command_name.split()[-1] == 'list' and 'ids' in linter.get_command_parameters(command_name):
        raise RuleError('List commands should not expose --ids argument')


@CommandRule(LinterSeverity.HIGH)
def expired_command(linter, command_name):
    if linter.command_expired(command_name):
        raise RuleError('Deprecated command is expired and should be removed.')
