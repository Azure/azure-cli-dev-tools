# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from ..rule_decorators import ParameterRule
from ..linter import RuleError, LinterSeverity
from knack.deprecation import Deprecated


@ParameterRule(LinterSeverity.HIGH)
def missing_parameter_help(linter, command_name, parameter_name):
    if not linter.get_parameter_help(command_name, parameter_name) and not linter.command_expired(command_name):
        raise RuleError('Missing help')


@ParameterRule(LinterSeverity.HIGH)
def expired_parameter(linter, command_name, parameter_name):
    if linter.parameter_expired(command_name, parameter_name):
        raise RuleError('Deprecated parameter is expired and should be removed.')


@ParameterRule(LinterSeverity.HIGH)
def expired_option(linter, command_name, parameter_name):
    expired_options = linter.option_expired(command_name, parameter_name)
    if expired_options:
        raise RuleError("Deprecated options '{}' are expired and should be removed.".format(', '.join(expired_options)))


@ParameterRule(LinterSeverity.HIGH)
def bad_short_option(linter, command_name, parameter_name):
    bad_options = []
    for option in linter.get_parameter_options(command_name, parameter_name):
        if isinstance(option, Deprecated):
            # we don't care if deprecated options are "bad options" since this is the
            # mechanism by which we get rid of them
            continue
        if not option.startswith('--') and len(option) != 2:
            bad_options.append(option)

    if bad_options:
        raise RuleError('Found multi-character short options: {}. Use a single character or '
                        'convert to a long-option.'.format(' | '.join(bad_options)))


@ParameterRule(LinterSeverity.HIGH)
def parameter_should_not_end_in_resource_group(linter, command_name, parameter_name):
    parameter = linter._command_loader.command_table[command_name].arguments[parameter_name].type.settings
    options_list = parameter.get('options_list', [])
    bad_options = []

    for opt in options_list:
        if isinstance(opt, Deprecated):
            # we don't care if deprecated options are "bad options" since this is the
            # mechanism by which we get rid of them
            continue
        if any([opt.endswith('resource-group'), opt.endswith('resourcegroup')]) and opt != "--resource-group":
            bad_options.append(opt)

    if bad_options:
        bad_options_str = ' | '.join(bad_options)
        raise RuleError("A command should only have '--resource-group' as its resource group parameter. "
                        "However options '{}' in command '{}' end with 'resource-group' or similar."
                        .format(bad_options_str, command_name))


@ParameterRule(LinterSeverity.HIGH)
def no_positional_parameters(linter, command_name, parameter_name):
    parameter = linter._command_loader.command_table[command_name].arguments[parameter_name].type.settings
    options_list = parameter.get('options_list', [])

    if not options_list:
        raise RuleError("CLI commands should have optional parameters instead of positional parameters "
                        "However parameter '{}' in command '{}' is a positional."
                        .format(parameter_name, command_name))