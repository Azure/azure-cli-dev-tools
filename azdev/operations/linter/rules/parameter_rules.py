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

        bad_opts = [opt.endswith('resource-group'), opt.endswith('resourcegroup'), opt.endswith("resource-group-name")]
        if any(bad_opts) and opt != "--resource-group":
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
        raise RuleError("CLI commands should have optional parameters instead of positional parameters. "
                        "However parameter '{}' in command '{}' is a positional."
                        .format(parameter_name, command_name))



@ParameterRule(LinterSeverity.HIGH)
def no_parameter_defaults_for_update_commands(linter, command_name, parameter_name):
    if command_name.split()[-1].lower() == "update":
        parameter = linter._command_loader.command_table[command_name].arguments[parameter_name].type.settings
        default_val = parameter.get('default')
        if default_val:
            raise RuleError("Update commands should not have parameters with default values. {} in {} has a "
                            "default value of '{}'".format(parameter_name, command_name, default_val))


@ParameterRule(LinterSeverity.MEDIUM)
def no_required_location_param(linter, command_name, parameter_name):
    # Location parameters should not be required

    has_resource_group = "resource_group_name" in linter._parameters[command_name]
    is_location_param = (parameter_name.lower() == "location" or parameter_name.endswith("location"))

    if has_resource_group and is_location_param:
        parameter = linter._command_loader.command_table[command_name].arguments[parameter_name].type.settings
        is_required = parameter.get('required')

        if is_required:
            raise RuleError("Location parameters should not be required. However, {} in {} should is required. "
                            "Please make it optional and default to the location of the resource group."
                            .format(parameter_name, command_name))


@ParameterRule(LinterSeverity.LOW)
def id_params_only_for_guid(linter, command_name, parameter_name):
    # Check if the parameter is an id param, except for '--ids'. If so, attempt to figure out if
    # it is a resource id parametere. This check can lead to false positives, which is why it is a low severity check.
    # Its aim is to guide reviewers and developers.

    def _help_contains_queries(help_strings, queries):
        a_query_is_in_a_str = next((True for help_str in help_strings
                                    for query in queries if query.lower() in help_str.lower()), False)
        return a_query_is_in_a_str

    parameter = linter._command_loader.command_table[command_name].arguments[parameter_name].type.settings
    options_list = parameter.get('options_list', [])
    queries = ["resource id", "arm id"]
    is_id_param = False

    # first find out if an option ends with id.
    for opt in options_list:
        if isinstance(opt, Deprecated):
            return

        id_opts = [opt.endswith('-id'), opt.endswith('-ids')]

        if any(id_opts) and opt != "--ids":
            is_id_param = True

    # if an option is an id param, check if the help text makes reference to 'resource id' etc. This could lead to fa
    if is_id_param:
        help_obj = linter._loaded_help[command_name]
        help_param = next((help_param_obj for help_param_obj in help_obj.parameters
                               if help_param_obj == " ".join(options_list)), None)

        if help_param and _help_contains_queries([help_param.short_summary, help_param.long_summary], queries):
            raise RuleError("An option {} ends with '-id'. Arguments ending with '-id' "
                            "must be guids/uuids and not resource ids.", options_list)