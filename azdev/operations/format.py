# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from glob import glob
import multiprocessing
import os
import sys

from knack.log import get_logger
from knack.util import CLIError, CommandResultItem

from azdev.utilities import (
    display, heading, py_cmd, get_path_table, EXTENSION_PREFIX,
    get_azdev_config, get_azdev_config_dir, require_azure_cli, filter_by_git_diff)


logger = get_logger(__name__)


# pylint: disable=too-many-statements
def auto_format(modules=None, git_source=None, git_target=None, git_repo=None):

    heading('Style Check')

    # allow user to run only on CLI or extensions
    cli_only = modules == ['CLI']
    ext_only = modules == ['EXT']
    if cli_only or ext_only:
        modules = None

    selected_modules = get_path_table(include_only=modules)

    # remove these two non-modules
    selected_modules['core'].pop('azure-cli-nspkg', None)
    selected_modules['core'].pop('azure-cli-command_modules-nspkg', None)

    black_result = None

    if cli_only:
        ext_names = None
        selected_modules['ext'] = {}
    if ext_only:
        mod_names = None
        selected_modules['mod'] = {}
        selected_modules['core'] = {}

    # filter down to only modules that have changed based on git diff
    selected_modules = filter_by_git_diff(selected_modules, git_source, git_target, git_repo)

    if not any(selected_modules.values()):
        raise CLIError('No modules selected.')

    mod_names = list(selected_modules['mod'].keys()) + list(selected_modules['core'].keys())
    ext_names = list(selected_modules['ext'].keys())

    if mod_names:
        display('Modules: {}\n'.format(', '.join(mod_names)))
    if ext_names:
        display('Extensions: {}\n'.format(', '.join(ext_names)))

    exit_code_sum = 0
    black_result = _run_black(selected_modules)
    exit_code_sum += black_result.exit_code

    if black_result.error:
        logger.error(black_result.error.output.decode('utf-8'))
        logger.error('Black: FAILED\n')
    else:
        display('Black: PASSED\n')

    sys.exit(exit_code_sum)


def _run_black(modules):

    cli_paths = list(modules["core"].values()) + list(modules["mod"].values())
    ext_paths = list(modules["ext"].values())

    def run(paths, rcfile, desc):
        if not paths:
            return None
        logger.debug("Running on %s:\n%s", desc, "\n".join(paths))
        command = "black -l 120 {}".format(
            " ".join(paths)
        )
        return py_cmd(command, message="Running black on {}...".format(desc))

    cli_config, ext_config = _config_file_path("black")

    cli_result = run(cli_paths, cli_config, "modules")
    ext_result = run(ext_paths, ext_config, "extensions")
    return _combine_command_result(cli_result, ext_result)
