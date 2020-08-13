# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import time

from knack.util import CLIError
from knack.log import get_logger

from azdev.utilities import (display, get_path_table, require_azure_cli, filter_by_git_diff)
from azdev.utilities.path import get_cli_repo_path

from azdev.operations.linter.util import filter_modules

logger = get_logger(__name__)


def test_coverage(modules=None, git_source=None, git_target=None, git_repo=None, include_whl_extensions=False,
                  save_global_exclusion=False):
    import mock
    exclusion_path = os.path.join(*[get_cli_repo_path(), 'test_exclusions.json'])

    with mock.patch('azure.cli.core.commands.validators.validate_file_or_dict', return_value={}),\
            mock.patch('azure.cli.core.util.get_json_object', return_value={}),\
            mock.patch('azure.cli.command_modules.keyvault._validators.certificate_type', return_value="fake-cert"):
        command_loader = load_command_table_and_command_loader(modules,
                                                               git_source,
                                                               git_target,
                                                               git_repo,
                                                               include_whl_extensions)
        simple_command_table = format_command_table(command_loader.command_table)
        parser = command_loader.cli_ctx.invocation.parser
        commands_without_tests = []

        test_exclusions = load_exclusions(exclusion_path)

        for ns in load_test_commands(parser):
            update_command_table(simple_command_table, ns)

        logger.warning("-------Test Results:-------")
        calculate_command_coverage_rate(simple_command_table, commands_without_tests, test_exclusions)
        if save_global_exclusion:
            save_commands_without_tests(commands_without_tests)


def load_exclusions(exclusion_path):
    import json

    test_exclusions = []
    try:
        with open(exclusion_path) as json_file:
            test_exclusions = json.load(json_file)
    except (OSError, IOError):
        pass
    return test_exclusions


def load_test_commands(parser):
    TEST_COMMANDS = [get_cli_repo_path(), 'az_command_coverage.txt']
    path = os.path.join(*TEST_COMMANDS)

    with open(path) as file:
        import shlex
        from azdev.operations.linter.rules.help_rules import _process_command_args
        command = file.readline()
        while command:
            try:
                command_args = shlex.split(command, comments=True)  # split commands into command args, ignore comments.
                command_args, _ = _process_command_args(command_args)
                ns = parser.parse_args(command_args)
                yield ns
            except:  # pylint: disable=bare-except
                logger.debug(command)
            command = file.readline()


def load_command_table_and_command_loader(modules=None, git_source=None,
                                          git_target=None, git_repo=None, include_whl_extensions=False):
    require_azure_cli()

    from azure.cli.core import get_default_cli  # pylint: disable=import-error
    from azure.cli.core.file_util import create_invoker_and_load_cmds_and_args  # pylint: disable=import-error

    # allow user to run only on CLI or extensions
    cli_only = modules == ['CLI']
    ext_only = modules == ['EXT']
    if cli_only or ext_only:
        modules = None

    selected_modules = get_path_table(include_only=modules, include_whl_extensions=include_whl_extensions)

    if cli_only:
        selected_modules['ext'] = {}
    if ext_only:
        selected_modules['mod'] = {}
        selected_modules['core'] = {}

        # filter down to only modules that have changed based on git diff
    selected_modules = filter_by_git_diff(selected_modules, git_source, git_target, git_repo)

    if not any((selected_modules[x] for x in selected_modules)):
        raise CLIError('No modules selected.')

    selected_mod_names = list(selected_modules['mod'].keys()) + list(selected_modules['core'].keys()) + \
                         list(selected_modules['ext'].keys())

    if selected_mod_names:
        display('Modules: {}\n'.format(', '.join(selected_mod_names)))

    display('Initializing linter with command table and help files...')
    az_cli = get_default_cli()

    # load commands, args, and help
    create_invoker_and_load_cmds_and_args(az_cli)

    command_loader = az_cli.invocation.commands_loader

    # load yaml help
    help_file_entries = {}

    # trim command table and help to just selected_modules
    command_loader, help_file_entries = filter_modules(
        command_loader, help_file_entries, modules=selected_mod_names, include_whl_extensions=include_whl_extensions)

    if not command_loader.command_table:
        raise CLIError('No commands selected to check.')
    return command_loader


def format_command_table(command_table):
    simple_command_table = {}
    ignore_arg = ['_subscription', 'cmd']
    for command, value in command_table.items():
        args_table = {arg: False for arg in value.arguments.keys() if arg not in ignore_arg}
        simple_command_table[command] = [args_table, False] # arg table and is the command tested
    return simple_command_table


def update_command_table(simple_command_table, namespace):
    command = namespace.command
    from knack.validators import DefaultInt, DefaultStr
    if command in simple_command_table:
        simple_command_table[command][1] = True
        for key in simple_command_table[command][0].keys():
            if all([hasattr(namespace, key),
                    getattr(namespace, key),
                    not isinstance(getattr(namespace, key), DefaultInt),
                    not isinstance(getattr(namespace, key), DefaultStr)]):
                simple_command_table[command][0][key] = True


def calculate_command_coverage_rate(simple_command_table, commands_without_tests, test_exclusions):
    command_coverage = {}
    for command, value in simple_command_table.items():
        command_group = command.split(' ')[0]
        if command_group not in command_coverage:
            command_coverage[command_group] = [0, 0]
        command_coverage[command_group][1] += 1
        if value[1]:
            command_coverage[command_group][0] += 1
        else:
            commands_without_tests.append(command)
            if command in test_exclusions:
                command_coverage[command_group][0] += 1
            else:
                logger.warning("% doesn't have test", command)
                continue


def save_commands_without_tests(commands_without_tests):
    import json
    file_name = os.path.join('.', 'commands_without_tests.json')
    with open(file_name, 'w') as out:
        json.dump(commands_without_tests, out)
