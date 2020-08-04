# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import sys
import time
import yaml

from knack.help_files import helps
from knack.log import get_logger
from knack.util import CLIError

from azdev.utilities import (
    heading, subheading, display, get_path_table, require_azure_cli, filter_by_git_diff)
from azdev.utilities.path import get_cli_repo_path, get_ext_repo_paths

from .linter import LinterManager, LinterScope, RuleError, LinterSeverity
from .util import filter_modules, merge_exclusion


logger = get_logger(__name__)
TEST_COMMANDS = [get_cli_repo_path(), 'az_command_coverage.txt']
CLI_SUPRESS = [get_cli_repo_path(), 'test_exclusions.json']

# pylint:disable=too-many-locals, too-many-statements, too-many-branches
def run_linter(modules=None, rule_types=None, rules=None, ci_exclusions=None,
               git_source=None, git_target=None, git_repo=None, include_whl_extensions=False,
               min_severity=None, save_global_exclusion=False):

    require_azure_cli()

    from azure.cli.core import get_default_cli  # pylint: disable=import-error
    from azure.cli.core.file_util import (  # pylint: disable=import-error
        get_all_help, create_invoker_and_load_cmds_and_args)

    heading('CLI Linter')

    # allow user to run only on CLI or extensions
    cli_only = modules == ['CLI']
    ext_only = modules == ['EXT']
    if cli_only or ext_only:
        modules = None

    # process severity option
    if min_severity:
        try:
            min_severity = LinterSeverity.get_linter_severity(min_severity)
        except ValueError:
            valid_choices = linter_severity_choices()
            raise CLIError("Please specify a valid linter severity. It should be one of: {}"
                           .format(", ".join(valid_choices)))

    # needed to remove helps from azdev
    azdev_helps = helps.copy()
    exclusions = {}
    selected_modules = get_path_table(include_only=modules, include_whl_extensions=include_whl_extensions)

    if cli_only:
        selected_modules['ext'] = {}
    if ext_only:
        selected_modules['mod'] = {}
        selected_modules['core'] = {}

    # used to upsert global exclusion
    update_global_exclusion = None
    if save_global_exclusion and (cli_only or ext_only):
        if cli_only:
            update_global_exclusion = 'CLI'
            if os.path.exists(os.path.join(get_cli_repo_path(), 'linter_exclusions.yml')):
                os.remove(os.path.join(get_cli_repo_path(), 'linter_exclusions.yml'))
        elif ext_only:
            update_global_exclusion = 'EXT'
            for ext_path in get_ext_repo_paths():
                if os.path.exists(os.path.join(ext_path, 'linter_exclusions.yml')):
                    os.remove(os.path.join(ext_path, 'linter_exclusions.yml'))

    # filter down to only modules that have changed based on git diff
    selected_modules = filter_by_git_diff(selected_modules, git_source, git_target, git_repo)

    if not any((selected_modules[x] for x in selected_modules)):
        logger.warning('No commands selected to check.')

    selected_mod_names = list(selected_modules['mod'].keys()) + list(selected_modules['core'].keys()) + \
        list(selected_modules['ext'].keys())
    selected_mod_paths = list(selected_modules['mod'].values()) + list(selected_modules['core'].values()) + \
        list(selected_modules['ext'].values())

    if selected_mod_names:
        display('Modules: {}\n'.format(', '.join(selected_mod_names)))

    # collect all rule exclusions
    for path in selected_mod_paths:
        exclusion_path = os.path.join(path, 'linter_exclusions.yml')
        if os.path.isfile(exclusion_path):
            mod_exclusions = yaml.safe_load(open(exclusion_path))
            merge_exclusion(exclusions, mod_exclusions or {})

    global_exclusion_paths = [os.path.join(get_cli_repo_path(), 'linter_exclusions.yml')]
    try:
        global_exclusion_paths.extend([os.path.join(path, 'linter_exclusions.yml')
                                       for path in (get_ext_repo_paths() or [])])
    except CLIError:
        pass
    for path in global_exclusion_paths:
        if os.path.isfile(path):
            mod_exclusions = yaml.safe_load(open(path))
            merge_exclusion(exclusions, mod_exclusions or {})

    start = time.time()
    display('Initializing linter with command table and help files...')
    az_cli = get_default_cli()

    # load commands, args, and help
    create_invoker_and_load_cmds_and_args(az_cli)
    loaded_help = get_all_help(az_cli)

    stop = time.time()
    logger.info('Commands and help loaded in %i sec', stop - start)
    command_loader = az_cli.invocation.commands_loader

    # format loaded help
    loaded_help = {data.command: data for data in loaded_help if data.command}

    # load yaml help
    help_file_entries = {}
    for entry_name, help_yaml in helps.items():
        # ignore help entries from azdev itself, unless it also coincides
        # with a CLI or extension command name.
        if entry_name in azdev_helps and entry_name not in command_loader.command_table:
            continue
        help_entry = yaml.safe_load(help_yaml)
        help_file_entries[entry_name] = help_entry

    # trim command table and help to just selected_modules
    command_loader, help_file_entries = filter_modules(
        command_loader, help_file_entries, modules=selected_mod_names, include_whl_extensions=include_whl_extensions)

    if not command_loader.command_table:
        logger.warning('No commands selected to check.')

    # Instantiate and run Linter
    linter_manager = LinterManager(command_loader=command_loader,
                                   help_file_entries=help_file_entries,
                                   loaded_help=loaded_help,
                                   exclusions=exclusions,
                                   rule_inclusions=rules,
                                   use_ci_exclusions=ci_exclusions,
                                   min_severity=min_severity,
                                   update_global_exclusion=update_global_exclusion)

    subheading('Results')
    logger.info('Running linter: %i commands, %i help entries',
                len(command_loader.command_table), len(help_file_entries))
    exit_code = linter_manager.run(
        run_params=not rule_types or 'params' in rule_types,
        run_commands=not rule_types or 'commands' in rule_types,
        run_command_groups=not rule_types or 'command_groups' in rule_types,
        run_help_files_entries=not rule_types or 'help_entries' in rule_types)
    sys.exit(exit_code)


def linter_severity_choices():
    return [str(severity.name).lower() for severity in LinterSeverity]


def command_test_coverage(modules=None, git_source=None, git_target=None, git_repo=None, include_whl_extensions=False,
                          save_global_exclusion=False):
    import mock

    with mock.patch('azure.cli.core.commands.validators.validate_file_or_dict', return_value={}),\
            mock.patch('azure.cli.core.util.get_json_object', return_value={}),\
            mock.patch('azure.cli.command_modules.keyvault._validators.certificate_type', return_value="fakecert"):
        import json
        require_azure_cli()

        from azure.cli.core import get_default_cli  # pylint: disable=import-error
        from azure.cli.core.file_util import (  # pylint: disable=import-error
            get_all_help, create_invoker_and_load_cmds_and_args)
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

        start = time.time()
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
        simple_command_table = _format_command_table(command_loader.command_table)
        parser = command_loader.cli_ctx.invocation.parser
        path = os.path.join(*TEST_COMMANDS)

        commands_without_tests = []
        test_exclusions = []

        try:
            with open(os.path.join(*CLI_SUPRESS)) as json_file:
                test_exclusions = json.load(json_file)
        except:
            pass

        with open(path) as file:
            import shlex
            from azdev.operations.linter.rules.help_rules import _process_command_args
            command = file.readline()
            while command:
                try:
                    command_args = shlex.split(command, comments=True)  # split commands into command args, ignore comments.
                    command_args, nested_commands = _process_command_args(command_args)
                    ns = parser.parse_args(command_args)
                    _update_command_table(simple_command_table, ns)
                except:
                    print(command)
                    pass
                command = file.readline()
        print("-------Test Results:-------")
        _calculate_command_coverage_rate(simple_command_table, commands_without_tests, test_exclusions)
        if save_global_exclusion:
            _save_commands_without_tests(commands_without_tests)


def _format_command_table(command_table):
    simple_command_table = {}
    ignore_arg = ['_subscription', 'cmd']
    for command, value in command_table.items():
        args_table = {arg: False for arg in value.arguments.keys() if arg not in ignore_arg}
        simple_command_table[command] = [args_table, False] # arg table and is the command tested
    return simple_command_table


def _update_command_table(simple_command_table, namespace):
    command = namespace.command
    from knack.validators import DefaultInt, DefaultStr
    if command in simple_command_table:
        simple_command_table[command][1] = True
        for key in simple_command_table[command][0].keys():
            if hasattr(namespace, key) and getattr(namespace, key) and (type(getattr(namespace, key)) not in [DefaultInt, DefaultStr]):
                simple_command_table[command][0][key] = True


def _calculate_command_coverage_rate(simple_command_table, commands_without_tests, test_exclusions):
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
                # print("{} doesn't have test".format(command))
                continue
    for command_group, value in command_coverage.items():
        print("{} command coverage is {}".format(command_group, value[0]*1.0/value[1]))


def _save_commands_without_tests(commands_without_tests):
    import json
    file_name = os.path.join('.', 'commands_without_tests.json')
    with open(file_name, 'w') as out:
        json.dump(commands_without_tests, out)