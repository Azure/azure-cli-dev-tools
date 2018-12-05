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
    get_env_config_dir, get_env_config)

logger = get_logger(__name__)


def _prompt_to_clone_repo(name, path):
    if prompt_y_n("Repo '{}' does not exist at path '{}'. Clone?".format(name, path)):
        return True
    else:
        raise CLIError("Operation aborted.")


def _clone_repo(name, path):
    message = "Cloning repo {} at path: {}".format(name, path)
    command = "git clone https://github.com/Azure/{}.git {}".format(name, path)
    cmd(command, message)


def _prompt_to_create_venv(name, path):
    if prompt_y_n("Virtual environment '{}' does not exist at path '{}'. Create?".format(name, path)):
        return True
    else:
        raise CLIError("Operation aborted.")


def _create_venv(path):
    message = "\nCreating virtual environment: {}".format(path)
    command = "virtualenv {}".format(path)
    py_cmd(command, message)


def _get_path(path, file_name, default):
    if not path:
        return None, None
    if path == Flag:
        path = find_file(file_name) or default
    path = os.path.abspath(path)
    exists = os.path.isdir(path)
    return path, exists


def _check_repo(path):
    if not os.path.isdir(os.path.join(path, ".git")):
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


def _extension_only_install():
    # TODO: Need to install azure-cli-testsdk (not currently on PyPI)
    pip_cmd("install -q azure-cli", "Installing `azure-cli`...")


def _cli_and_extension_install(cli_path, ext_path):
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


def _get_venv_activate_command(venv):
    return os.path.join(venv, "Scripts" if IS_WINDOWS else "bin", "activate")


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


def setup(cmd, venv='env', cli_path=None, ext_path=None, yes=None):

    start = time.time()

    heading('Azure CLI Dev Setup')

    if not (cli_path or ext_path):
        raise CLIError("usage error: must specify at least one of --cli or --ext")

    cli_path, cli_exists = _get_path(cli_path, 'azure-cli.pyproj', 'azure-cli')
    ext_path, ext_exists = _get_path(ext_path, 'azure-cli-extensions.pyproj', 'azure-cli-extensions')

    cli_clone = False
    ext_clone = False
    create_venv = False

    if cli_path:
        if cli_exists:
            _check_repo(cli_path)
            display("Azure CLI repo found at: {}".format(cli_path))
        else:
            cli_clone = _prompt_to_clone_repo("azure-cli", cli_path)

    if ext_path:
        if ext_exists:
            _check_repo(ext_path)
            display("Azure CLI extensions repo found at: {}".format(ext_path))
        else:
            ext_clone = _prompt_to_clone_repo("azure-cli-extensions", ext_path)

    # setup virtual environment or use existing
    env_path = os.path.abspath(venv)
    if not os.path.isdir(env_path):
        create_venv = _prompt_to_create_venv(venv, env_path)
    else:
        display("Virtual environment found at: {}".format(env_path))

    # perform any cloning or venv creation
    if cli_clone:
        _clone_repo("azure-cli", cli_path)
    if ext_clone:
        _clone_repo("azure-cli-extensions", ext_path)
    if create_venv:
        _create_venv(env_path)
        logger.warning(
            "Virtual environment created. Run `{}` and then re-run this command to continue.".format(
                _get_venv_activate_command(venv)
            )
        )
        sys.exit(0)

    # before any packages can be pip installed, the desired virtual environment must be activated by the user
    virtual_env_var = os.environ.get("VIRTUAL_ENV", None)
    if env_path != virtual_env_var:
        raise CLIError(
            "To continue with CLI setup, you must activate the virtual environment by running `{}`".format(
                _get_venv_activate_command(venv)
            )
        )
    config = get_env_config()

    # save data to config files
    if ext_path:
        from azdev.utilities import get_azure_config
        config.set_value('ext', 'repo_path', ext_path)
        az_config = get_azure_config()
        az_config.set_value('extension', 'dev_sources', os.path.join(ext_path))

    if cli_path:
        config.set_value('cli', 'repo_path', cli_path)

    # install packages
    heading('Installing packages')

    if ext_path and not cli_path:
        _extension_only_install()
    else:
        _cli_and_extension_install(cli_path, ext_path)

    # TODO: Final step, re-install azdev in the virtual environment
    # in order to have all needed packages.

    _copy_config_files()

    end = time.time()
    elapsed_min = int((end - start) / 60)
    elapsed_sec = int(end - start) % 60
    display('\nElapsed time: {} min {} sec'.format(elapsed_min, elapsed_sec))

    heading('Finished dev setup!')


def configure(cmd, cli_path=None, ext_path=None):

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
