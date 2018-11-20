# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

# import automation.utilities.path as automation_path

import multiprocessing
import os
import sys

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


from azdev.utilities import (
    display, heading, subheading, py_cmd, get_core_module_paths, get_command_module_paths, get_extension_paths,
    filter_module_paths)


def check_style(cmd, modules=None, pylint=False, pep8=False):

    cli_path = cmd.cli_ctx.config.get('cli', 'repo_path')
    ext_path = cmd.cli_ctx.config.get('ext', 'repo_path')

    heading('Style Check')

    all_modules = get_command_module_paths() + get_core_module_paths() + get_extension_paths()
    pep8_result = None
    pylint_result = None

    selected_modules = filter_module_paths(all_modules, modules)

    if not selected_modules:
        raise CLIError('No modules selected.')

    display('Modules: {}\n'.format(', '.join(name for name, _ in selected_modules)))

    # if neither flag provided, same as if both were provided
    if not any([pylint, pep8]):
        pep8 = True
        pylint = True

    exit_code_sum = 0
    if pep8:
        pep8_result = _run_pep8(cli_path, ext_path, selected_modules)
        exit_code_sum += pep8_result.exit_code

    if pylint:
        pylint_result = _run_pylint(cli_path, ext_path, selected_modules)
        exit_code_sum += pylint_result.exit_code

    display('')
    subheading('Results')

    # print success messages first
    if pep8_result and not pep8_result.error:
        display('Flake8: PASSED')
    if pylint_result and not pylint_result.error:
        display('Pylint: PASSED')

    display('')

    # print error messages last
    if pep8_result and pep8_result.error:
        logger.error(pep8_result.error.output)
        logger.error('Flake8: FAILED')
    if pylint_result and pylint_result.error:
        logger.error(pylint_result.error.output)
        logger.error('Pylint: FAILED')

    sys.exit(exit_code_sum)


def _run_pylint(cli_path, ext_path, modules):

    # TODO: Update to use ext_path as well
    modules_list = ' '.join(
        [os.path.join(path, 'azure') for name, path in modules if not name.endswith('-nspkg')])
    command = 'pylint {} --rcfile={} -j {}'.format(
        modules_list,
        os.path.join(cli_path, 'pylintrc'),
        multiprocessing.cpu_count())

    return py_cmd(command, message='Running pylint...', show_stderr=True)


def _run_pep8(cli_path, ext_path, modules):

    # TODO: Update to use ext_path as well
    command = 'flake8 --statistics --append-config={} {}'.format(
        os.path.join(cli_path, '.flake8'),
        ' '.join(path for _, path in modules))

    return py_cmd(command, message='Running flake8...', show_stderr=True)
