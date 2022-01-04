# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------


import time

from knack.log import get_logger
from azdev.utilities import (
    heading, display, get_path_table, require_azure_cli, filter_by_git_diff)
from azdev.operations.constant import EXCLUDE_MODULES
from .cmdcov import CmdcovManager

logger = get_logger(__name__)


# pylint:disable=too-many-locals, too-many-statements, too-many-branches
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

    heading('CLI Command Coverage')

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

    cmdcov_manager = CmdcovManager(selected_mod_names=selected_mod_names,
                                   selected_mod_paths=selected_mod_paths,
                                   loaded_help=loaded_help,
                                   level=level,
                                   enable_cli_own=enable_cli_own)
    cmdcov_manager.run()


if __name__ == '__main__':
    pass
    # _get_all_tested_commands(['a'], ['b'])
    # regex2()
    # regex3()
