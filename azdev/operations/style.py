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
    display, heading, subheading, py_cmd, get_path_table, EXTENSION_PREFIX,
    get_azdev_config_dir, require_azure_cli)


logger = get_logger(__name__)


def check_style(modules=None, pylint=False, pep8=False):

    heading('Style Check')

    selected_modules = get_path_table(include_only=modules)
    pep8_result = None
    pylint_result = None

    if pylint:
        try:
            require_azure_cli()
        except CLIError:
            raise CLIError('usage error: --pylint requires Azure CLI to be installed.')

    if not selected_modules:
        raise CLIError('No modules selected.')

    mod_names = list(selected_modules['mod'].keys()) + list(selected_modules['core'].keys())
    ext_names = list(selected_modules['ext'].keys())
    if mod_names:
        display('Modules: {}\n'.format(', '.join(mod_names)))
    if ext_names:
        display('Extensions: {}\n'.format(', '.join(ext_names)))

    # if neither flag provided, same as if both were provided
    if not any([pylint, pep8]):
        pep8 = True
        pylint = True

    exit_code_sum = 0
    if pep8:
        pep8_result = _run_pep8(selected_modules)
        exit_code_sum += pep8_result.exit_code

    if pylint:
        pylint_result = _run_pylint(selected_modules)
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
        logger.error(pep8_result.error.output.decode('utf-8'))
        logger.error('Flake8: FAILED\n')
    if pylint_result and pylint_result.error:
        logger.error(pylint_result.error.output.decode('utf-8'))
        logger.error('Pylint: FAILED\n')

    sys.exit(exit_code_sum)


def _combine_command_result(cli_result, ext_result):

    final_result = CommandResultItem(None)

    def apply_result(item):
        if item:
            final_result.exit_code += item.exit_code
            if item.error:
                if final_result.error:
                    final_result.error.message += item.error.message
                else:
                    final_result.error = item.error
            if item.result:
                if final_result.result:
                    final_result.result += item.result
                else:
                    final_result.result = item.result
    apply_result(cli_result)
    apply_result(ext_result)
    return final_result


def _run_pylint(modules):

    cli_paths = []
    for path in list(modules['core'].values()) + list(modules['mod'].values()):
        cli_paths.append(os.path.join(path, 'azure'))

    ext_paths = []
    for path in list(modules['ext'].values()):
        glob_pattern = os.path.normcase(os.path.join('{}*'.format(EXTENSION_PREFIX)))
        ext_paths.append(glob(os.path.join(path, glob_pattern))[0])

    def run(paths, rcfile, desc):
        if not paths:
            return None
        config_path = os.path.join(get_azdev_config_dir(), 'config_files', rcfile)
        logger.info('Using rcfile file: %s', config_path)
        logger.info('Running on %s: %s', desc, ' '.join(paths))
        command = 'pylint {} --ignore vendored_sdks,privates --rcfile={} -j {}'.format(
            ' '.join(paths),
            config_path,
            multiprocessing.cpu_count())
        return py_cmd(command, message='Running pylint on {}...'.format(desc))

    cli_result = run(cli_paths, 'cli_pylintrc', 'modules')
    ext_result = run(ext_paths, 'ext_pylintrc', 'extensions')
    return _combine_command_result(cli_result, ext_result)


def _run_pep8(modules):

    cli_paths = list(modules['core'].values()) + list(modules['mod'].values())
    ext_paths = list(modules['ext'].values())

    def run(paths, config_file, desc):
        if not paths:
            return None
        config_path = os.path.join(get_azdev_config_dir(), 'config_files', config_file)
        logger.info('Using config file: %s', config_path)
        logger.info('Running on %s: %s', desc, ' '.join(paths))
        command = 'flake8 --statistics --append-config={} {}'.format(
            config_path,
            ' '.join(paths))
        return py_cmd(command, message='Running flake8 on {}...'.format(desc))

    cli_result = run(cli_paths, 'cli.flake8', 'modules')
    ext_result = run(ext_paths, 'ext.flake8', 'extensions')
    return _combine_command_result(cli_result, ext_result)
