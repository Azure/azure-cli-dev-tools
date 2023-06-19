# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import time
import yaml

from knack.log import get_logger
from knack.util import CLIError
from azdev.utilities import (
    heading, display, get_path_table, require_azure_cli, filter_by_git_diff)
from azdev.utilities.path import get_cli_repo_path, get_ext_repo_paths
from .cmdcov import CmdcovManager


logger = get_logger(__name__)
try:
    with open(os.path.join(get_cli_repo_path(), 'scripts', 'ci', 'cmdcov.yml'), 'r') as file:
        config = yaml.safe_load(file)
        EXCLUDE_MODULES = config['EXCLUDE_MODULES']
except CLIError as ex:
    logger.warning('Failed to load cmdcov.yml: %s', ex)


# pylint:disable=too-many-locals, too-many-statements, too-many-branches, duplicate-code
def run_cmdcov(modules=None, git_source=None, git_target=None, git_repo=None, level='command'):
    """
    :param modules:
    :param git_source:
    :param git_target:
    :param git_target:
    :return: None
    """
    require_azure_cli()
    from azure.cli.core import get_default_cli  # pylint: disable=import-error
    from azure.cli.core.file_util import (  # pylint: disable=import-error
        get_all_help, create_invoker_and_load_cmds_and_args)

    heading('CLI Command Test Coverage')

    # allow user to run only on CLI or extensions
    cli_only = modules == ['CLI']
    # ext_only = modules == ['EXT']
    enable_cli_own = bool(cli_only or modules is None)
    if cli_only:
        modules = None
    # if cli_only or ext_only:
    #     modules = None

    selected_modules = get_path_table(include_only=modules)

    # filter down to only modules that have changed based on git diff
    selected_modules = filter_by_git_diff(selected_modules, git_source, git_target, git_repo)

    if not any(selected_modules.values()):
        logger.warning('No commands selected to check.')

    if EXCLUDE_MODULES:
        selected_modules['mod'] = {k: v for k, v in selected_modules['mod'].items() if k not in EXCLUDE_MODULES}
        selected_modules['ext'] = {k: v for k, v in selected_modules['ext'].items() if k not in EXCLUDE_MODULES}

    if cli_only:
        selected_mod_names = list(selected_modules['mod'].keys())
        selected_mod_paths = list(selected_modules['mod'].values())
    # elif ext_only:
    #     selected_mod_names = list(selected_modules['ext'].keys())
    #     selected_mod_paths = list(selected_modules['ext'].values())
    else:
        selected_mod_names = list(selected_modules['mod'].keys())
        selected_mod_paths = list(selected_modules['mod'].values())

    if selected_mod_names:
        display('Modules: {}\n'.format(', '.join(selected_mod_names)))

    start = time.time()
    display('Initializing cmdcov with command table and help files...')
    az_cli = get_default_cli()

    # load commands, args, and help
    create_invoker_and_load_cmds_and_args(az_cli)
    loaded_help = get_all_help(az_cli)

    stop = time.time()
    logger.info('Commands and help loaded in %i sec', stop - start)

    # format loaded help
    loaded_help = {data.command: data for data in loaded_help if data.command}

    linter_exclusions = {}

    # collect rule exclusions from selected mod paths
    for path in selected_mod_paths:
        mod_exclusion_path = os.path.join(path, 'linter_exclusions.yml')
        if os.path.isfile(mod_exclusion_path):
            with open(mod_exclusion_path) as f:
                mod_exclusions = yaml.safe_load(f)
            merge_exclusions(linter_exclusions, mod_exclusions or {})

    # collect rule exclusions from global exclusion paths
    global_exclusion_paths = [os.path.join(get_cli_repo_path(), 'linter_exclusions.yml')]
    try:
        global_exclusion_paths.extend([os.path.join(path, 'linter_exclusions.yml')
                                       for path in (get_ext_repo_paths() or [])])
    except CLIError:
        pass
    for path in global_exclusion_paths:
        if os.path.isfile(path):
            with open(path) as f:
                mod_exclusions = yaml.safe_load(f)
            merge_exclusions(linter_exclusions, mod_exclusions or {})

    cmdcov_manager = CmdcovManager(selected_mod_names=selected_mod_names,
                                   selected_mod_paths=selected_mod_paths,
                                   loaded_help=loaded_help,
                                   level=level,
                                   enable_cli_own=enable_cli_own,
                                   exclusions=linter_exclusions)
    cmdcov_manager.run()


# pylint: disable=line-too-long
def merge_exclusions(left_exclusion, right_exclusion):
    for command_name, value in right_exclusion.items():
        for rule_name in value.get('rule_exclusions', []):
            left_exclusion.setdefault(command_name, {}).setdefault('rule_exclusions', []).append(rule_name)
        for param_name in value.get('parameters', {}):
            for rule_name in value.get('parameters', {}).get(param_name, {}).get('rule_exclusions', []):
                left_exclusion.setdefault(command_name, {}).setdefault('parameters', {}).setdefault(param_name, {}).setdefault('rule_exclusions', []).append(rule_name)


if __name__ == '__main__':
    pass
    # _get_all_tested_commands(['a'], ['b'])
    # regex2()
    # regex3()
