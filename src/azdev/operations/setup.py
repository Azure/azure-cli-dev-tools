# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
from subprocess import CalledProcessError
from shutil import copytree, rmtree
import sys
import time

from knack.log import get_logger
from knack.prompting import prompt_y_n
from knack.util import CLIError

from azdev.params import Flag
from azdev.utilities import (
    display, heading, subheading, cmd, py_cmd, pip_cmd, find_file, IS_WINDOWS, get_path_table,
    get_env_config_dir, get_env_config, require_virtual_env, get_azure_config)

logger = get_logger(__name__)


def _check_path(path, file_name):
    """ Ensures the file_name is provided in the supplied path. """
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise CLIError('{} is not a valid path.'.format(path))
    _check_repo(path)
    if file_name not in os.listdir(path):
        raise CLIError("'{}' does not contain the expected file '{}'".format(path, file_name))
    return path


def _check_repo(path):
    if not os.path.isdir(os.path.join(path, '.git')):
        raise CLIError("'{}' is not a valid git repository.".format(path))


def _install_modules(cli_path):

    all_modules = list(get_path_table()['mod'].items())

    failures = []
    mod_num = 1
    total_mods = len(all_modules)
    for name, path in all_modules:
        try:
            pip_cmd("install -q -e {}".format(path), "Installing module `{}` ({}/{})...".format(name, mod_num, total_mods))
            mod_num += 1
        except CalledProcessError as err:
            # exit code is not zero
            failures.append("Failed to install {}. Error message: {}".format(name, err.output))

    for f in failures:
        display(f)

    return not any(failures)


def _install_extensions(ext_paths):
    for path in ext_paths or []:
        result = pip_cmd('install -e {}'.format(path), "Adding extension '{}'...".format(path))
        if result.error:
            raise result.error


def _install_cli(cli_path):

    # install public CLI off PyPI if no repo found
    if not cli_path:
        # TODO: Need to install azure-cli-testsdk (not currently on PyPI)
        return pip_cmd('install --upgrade azure-cli', "Installing `azure-cli`...")

    # otherwise editable install from source
    # install private whls if there are any
    privates_dir = os.path.join(cli_path, "privates")
    if os.path.isdir(privates_dir) and os.listdir(privates_dir):
        whl_list = " ".join(
            [os.path.join(privates_dir, f) for f in os.listdir(privates_dir)]
        )
        pip_cmd("install -q {}".format(whl_list), "Installing private whl files...")

    # install general requirements
    pip_cmd(
        "install -q -r {}/requirements.txt".format(cli_path),
        "Installing `requirements.txt`...",
    )

    # command modules have dependency on azure-cli-core so install this first
    pip_cmd(
        "install -q -e {}/src/azure-cli-nspkg".format(cli_path),
        "Installing `azure-cli-nspkg`...",
    )
    pip_cmd(
        "install -q -e {}/src/azure-cli-telemetry".format(cli_path),
        "Installing `azure-cli-telemetry`...",
    )
    pip_cmd(
        "install -q -e {}/src/azure-cli-core".format(cli_path),
        "Installing `azure-cli-core`...",
    )
    _install_modules(cli_path)

    # azure cli has dependencies on the above packages so install this one last
    pip_cmd(
        "install -q -e {}/src/azure-cli".format(cli_path), "Installing `azure-cli`..."
    )
    pip_cmd(
        "install -q -e {}/src/azure-cli-testsdk".format(cli_path),
        "Installing `azure-cli-testsdk`...",
    )

    # Ensure that the site package's azure/__init__.py has the old style namespace
    # package declaration by installing the old namespace package
    pip_cmd("install -q -I azure-nspkg==1.0.0", "Installing `azure-nspkg`...")
    pip_cmd("install -q -I azure-mgmt-nspkg==1.0.0", "Installing `azure-mgmt-nspkg`...")


def _copy_config_files():
    from glob import glob
    from importlib import import_module

    config_mod = import_module('azdev.config')
    config_dir_path = config_mod.__dict__['__path__'][0]
    dest_path = os.path.join(get_env_config_dir(), 'config_files')
    if os.path.exists(dest_path):
        rmtree(dest_path)
    copytree(config_dir_path, dest_path)
    # remove the python __init__ files
    pattern = os.path.join(dest_path, '*.py*')
    for path in glob(pattern):
        os.remove(path)


def setup(cmd, cli_path=None, ext_repo_path=None, ext=None):

    require_virtual_env()

    start = time.time()

    heading('Azure CLI Dev Setup')

    # TODO: if no parameters provided, proceed with interactive setup
    if not any([cli_path, ext_repo_path, ext]):
        raise CLIError('Interactive setup coming soon.')

    # otherwise assume programmatic setup
    if cli_path:
        CLI_SENTINEL = 'azure-cli.pyproj'
        if cli_path == Flag:
            cli_path = find_file(CLI_SENTINEL)
        cli_path = _check_path(cli_path, CLI_SENTINEL)
        display('Azure CLI:\n    {}\n'.format(cli_path))
    else:
        display('Azure CLI:\n    PyPI\n')

    # must add the necessary repo to add an extension
    if ext and not ext_repo_path:
        raise CLIError('usage error: --repo EXT_REPO [EXT_REPO ...] [--ext EXT_NAME ...]')

    if ext_repo_path:
        # add extension repo(s)
        from azdev.operations.extensions import add_extension_repo
        add_extension_repo(ext_repo_path)
        display('Azure CLI extension repos:\n    {}'.format('\n    '.join([os.path.abspath(x) for x in ext_repo_path])))

    ext_to_install = []
    if ext:
        # add extension(s)
        from azdev.operations.extensions import list_extensions
        available_extensions = [x['name'] for x in list_extensions()]
        not_found = [x for x in ext if x not in available_extensions]
        if not_found:
            raise CLIError("The following extensions were not found. Ensure you have added the repo using `--repo/-r PATH`.\n    {}".format('\n    '.join(not_found)))
        ext_to_install = [x['path'] for x in list_extensions() if x['name'] in ext]

    if ext_to_install:
        display('\nAzure CLI extensions:\n    {}'.format('\n    '.join(ext_to_install)))

    dev_sources = get_azure_config().get('extension', 'dev_sources', None)

    # save data to config files
    config  = get_env_config()
    config.set_value('ext', 'repo_path', dev_sources if dev_sources else '_NONE_')
    config.set_value('cli', 'repo_path', cli_path if cli_path else '_NONE_')

    # install packages
    subheading('Installing packages')

    # upgrade to latest pip
    pip_cmd('install --upgrade pip -q', 'Upgrading pip...')

    _install_cli(cli_path)
    _install_extensions(ext_to_install)
    _copy_config_files()

    end = time.time()
    elapsed_min = int((end - start) / 60)
    elapsed_sec = int(end - start) % 60
    display('\nElapsed time: {} min {} sec'.format(elapsed_min, elapsed_sec))

    subheading('Finished dev setup!')


def configure(cmd, cli_path=None, ext_path=None):

    require_virtual_env()

    heading('Azdev Configure')

    cli_path, cli_exists = _get_path(cli_path or Flag, 'azure-cli.pyproj', 'azure-cli')
    ext_path, ext_exists = _get_path(ext_path or Flag, 'azure-cli-extensions.pyproj', 'azure-cli-extensions')

    if cli_path and cli_exists:
        _check_repo(cli_path)
        display("Azure CLI repo found at: {}".format(cli_path))

    if ext_path and ext_exists:
        _check_repo(ext_path)
        display("Azure CLI extensions repo found at: {}".format(ext_path))

    # save data to config files
    config = get_env_config()
    if ext_path:
        from azdev.utilities import get_azure_config
        config.set_value('ext', 'repo_path', ext_path)
        az_config = get_azure_config()
        az_config.set_value('extension', 'dev_sources', os.path.join(ext_path))

    if cli_path:
        config.set_value('cli', 'repo_path', cli_path)

    _copy_config_files()

    subheading('Azdev configured!')
