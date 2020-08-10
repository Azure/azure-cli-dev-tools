
# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
from shutil import copytree, rmtree
import shutil
import time
import sys

from knack.log import get_logger
from knack.util import CLIError

from azdev.operations.extensions import (
    list_extensions, add_extension_repo, remove_extension)
from azdev.params import Flag
import azdev.utilities.const as const
import azdev.utilities.venv as venv
from azdev.utilities import (
    display, heading, subheading, pip_cmd, find_file, get_env_path,
    get_azdev_config_dir, get_azdev_config, get_azure_config, shell_cmd)

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


def _install_extensions(ext_paths):
    # clear pre-existing dev extensions
    try:
        installed_extensions = [x['name'] for x in list_extensions() if x['install'] == 'Y']
        remove_extension(installed_extensions)
    except KeyError as ex:
        logger.warning('Error occurred determining installed extensions. Run with --debug for more info.')
        logger.debug(ex)

    # install specified extensions
    for path in ext_paths or []:
        result = pip_cmd('install -e {}'.format(path), "Adding extension '{}'...".format(path))
        if result.error:
            raise result.error  # pylint: disable=raising-bad-type


def _install_cli(cli_path, deps=None):

    if not cli_path:
        # install public CLI off PyPI if no repo found
        pip_cmd('install --upgrade azure-cli', "Installing `azure-cli`...")
        pip_cmd('install git+https://github.com/Azure/azure-cli@master#subdirectory=src/azure-cli-testsdk',
                "Installing `azure-cli-testsdk`...")
        return
    if cli_path == 'EDGE':
        # install the public edge build
        pip_cmd('install --pre azure-cli --extra-index-url https://azurecliprod.blob.core.windows.net/edge',
                "Installing `azure-cli` edge build...")
        pip_cmd('install git+https://github.com/Azure/azure-cli@master#subdirectory=src/azure-cli-testsdk',
                "Installing `azure-cli-testsdk`...")
        return

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
        "Installing `requirements.txt`..."
    )
    if deps == 'setup.py':
        # Resolve dependencies from setup.py files.
        # command modules have dependency on azure-cli-core so install this first
        pip_cmd(
            "install -q -e {}/src/azure-cli-nspkg".format(cli_path),
            "Installing `azure-cli-nspkg`..."
        )
        pip_cmd(
            "install -q -e {}/src/azure-cli-telemetry".format(cli_path),
            "Installing `azure-cli-telemetry`..."
        )
        pip_cmd(
            "install -q -e {}/src/azure-cli-core".format(cli_path),
            "Installing `azure-cli-core`..."
        )

        # azure cli has dependencies on the above packages so install this one last
        pip_cmd("install -q -e {}/src/azure-cli".format(cli_path), "Installing `azure-cli`...")
        pip_cmd(
            "install -q -e {}/src/azure-cli-testsdk".format(cli_path),
            "Installing `azure-cli-testsdk`..."
        )
    else:
        # First install packages without dependencies,
        # then resolve dependencies from requirements.*.txt file.
        pip_cmd(
            "install -e {}/src/azure-cli-nspkg --no-deps".format(cli_path),
            "Installing `azure-cli-nspkg`..."
        )
        pip_cmd(
            "install -e {}/src/azure-cli-telemetry --no-deps".format(cli_path),
            "Installing `azure-cli-telemetry`..."
        )
        pip_cmd(
            "install -e {}/src/azure-cli-core --no-deps".format(cli_path),
            "Installing `azure-cli-core`..."
        )

        pip_cmd("install -e {}/src/azure-cli --no-deps".format(cli_path), "Installing `azure-cli`...")

        # The dependencies of testsdk are not in requirements.txt as this package is not needed by the
        # azure-cli package for running commands.
        # Here we need to install with dependencies for azdev test.
        pip_cmd(
            "install -e {}/src/azure-cli-testsdk".format(cli_path),
            "Installing `azure-cli-testsdk`..."
        )
        import platform
        system = platform.system()
        req_file = 'requirements.py3.{}.txt'.format(system)
        pip_cmd("install -r {}/src/azure-cli/{}".format(cli_path, req_file),
                "Installing `{}`...".format(req_file))

    # Ensure that the site package's azure/__init__.py has the old style namespace
    # package declaration by installing the old namespace package
    pip_cmd("install -q -I azure-nspkg==1.0.0", "Installing `azure-nspkg`...")
    pip_cmd("install -q -I azure-mgmt-nspkg==1.0.0", "Installing `azure-mgmt-nspkg`...")


def _copy_config_files():
    from glob import glob
    from importlib import import_module

    config_mod = import_module('azdev.config')
    config_dir_path = config_mod.__dict__['__path__'][0]
    dest_path = os.path.join(get_azdev_config_dir(), 'config_files')
    if os.path.exists(dest_path):
        rmtree(dest_path)
    copytree(config_dir_path, dest_path)
    # remove the python __init__ files
    pattern = os.path.join(dest_path, '*.py*')
    for path in glob(pattern):
        os.remove(path)


# pylint: disable=too-many-statements
def _interactive_setup():
    from knack.prompting import prompt_y_n, prompt
    while True:
        cli_path = None
        ext_repos = []
        exts = []

        # CLI Installation
        if prompt_y_n('Do you plan to develop CLI modules?'):
            display("\nGreat! Please enter the path to your azure-cli repo, 'EDGE' to install "
                    "the latest developer edge build or simply press "
                    "RETURN and we will attempt to find your repo for you.")
            while True:
                cli_path = prompt('\nPath (RETURN to auto-find): ', None)
                cli_path = os.path.abspath(os.path.expanduser(cli_path)) if cli_path else None
                CLI_SENTINEL = 'azure-cli.pyproj'
                if not cli_path:
                    cli_path = find_file(CLI_SENTINEL)
                if not cli_path:
                    raise CLIError('Unable to locate your CLI repo. Things to check:'
                                   '\n    Ensure you have cloned the repo. '
                                   '\n    Specify the path explicitly with `-c PATH`. '
                                   '\n    If you run with `-c` to autodetect, ensure you are running '
                                   'this command from a folder upstream of the repo.')
                try:
                    if cli_path != 'EDGE':
                        cli_path = _check_path(cli_path, CLI_SENTINEL)
                    display('Found: {}'.format(cli_path))
                    break
                except CLIError as ex:
                    logger.error(ex)
                    continue
        else:
            display('\nOK. We will install the latest `azure-cli` from PyPI then.')

        def add_ext_repo(path):
            try:
                _check_repo(path)
            except CLIError as ex:
                logger.error(ex)
                return False
            ext_repos.append(path)
            display('Repo {} OK.'.format(path))
            return True

        # Determine extension repos
        # Allows the user to simply press RETURN to use their cwd, assuming they are in their desired extension
        # repo directory. To use multiple extension repos or identify a repo outside the cwd, they must specify
        # the path.
        if prompt_y_n('\nDo you plan to develop CLI extensions?'):
            display('\nGreat! Input the path for the extension repos you wish to develop for. '
                    '(TIP: to quickly get started, press RETURN to '
                    'use your current working directory).')
            first_repo = True
            while True:
                msg = '\nPath ({}): '.format('RETURN to use current directory' if first_repo else 'RETURN to continue')
                ext_repo_path = prompt(msg, None)
                if not ext_repo_path:
                    if first_repo and not add_ext_repo(os.getcwd()):
                        first_repo = False
                        continue
                    break
                add_ext_repo(os.path.abspath(os.path.expanduser(ext_repo_path)))
                first_repo = False

        display('\nTIP: you can manage extension repos later with the `azdev extension repo` commands.')

        # Determine extensions
        if ext_repos:
            if prompt_y_n('\nWould you like to install certain extensions by default? '):
                display('\nGreat! Input the names of the extensions you wish to install, one per '
                        'line. You can add as many repos as you like. Use * to install all extensions. '
                        'Press RETURN to continue to the next step.')
                available_extensions = [x['name'] for x in list_extensions()]
                while True:
                    ext_name = prompt('\nName (RETURN to continue): ', None)
                    if not ext_name:
                        break
                    if ext_name == '*':
                        exts = [x['path'] for x in list_extensions()]
                        break
                    if ext_name not in available_extensions:
                        logger.error("Extension '%s' not found. Check the spelling, and make "
                                     "sure you added the repo first!", ext_name)
                        continue
                    display('Extension {} OK.'.format(ext_name))
                    exts.append(next(x['path'] for x in list_extensions() if x['name'] == ext_name))

            display('\nTIP: you can manage extensions later with the `azdev extension` commands.')

        subheading('Summary')
        display('CLI: {}'.format(cli_path if cli_path else 'PyPI'))
        display('Extension repos: {}'.format(' '.join(ext_repos)))
        display('Extensions: \n    {}'.format('\n    '.join(exts)))
        if prompt_y_n('\nProceed with installation? '):
            return cli_path, ext_repos, exts
        raise CLIError('Installation aborted.')


def _validate_input(cli_path, ext_repo_path, set_env, copy, use_global, ext):
    if not cli_path:
        raise CLIError("-c must be given if any other arguments are given")
    if copy and use_global:
        raise CLIError("Copy and use global are mutally exlcusive.")
    if cli_path == "pypi" and any([use_global, copy, set_env]):
        raise CLIError("pypi for cli path is mutally exlcusive with global copy and set env")
    if not cli_path and any([use_global, copy, set_env]):
        raise CLIError("if global, copy, or set env are set then both an extensions repo "
                       " and a cli repo must be specified")
    if not ext_repo_path and ext:
        raise CLIError("Extesions provided to be installed but no extensions path was given")


def _check_paths(cli_path, ext_repo_path):
    if not os.path.isdir(cli_path):
        raise CLIError("The cli path is not a valid directory, please check the path")
    if ext_repo_path and not os.path.isdir(ext_repo_path):
        raise CLIError("The cli extensions path is not a valid directory, please check the path")


def _check_shell():
    if const.SHELL in os.environ and const.IS_WINDOWS and const.BASH_NAME_WIN in os.environ[const.SHELL]:
        heading("WARNING: You are running bash in Windows, the setup may not work correctly and "
                "command may have unexpected behavior")
        from knack.prompting import prompt_y_n
        if not prompt_y_n('Would you like to continue with the install?'):
            sys.exit(0)


def setup(cli_path=None, ext_repo_path=None, ext=None, deps=None, set_env=None, copy=None, use_global=None):
    if not set_env:
        if not get_env_path():
            raise CLIError('You are not running in a virtual enviroment and have not chosen to set one up.')
    elif 'VIRTUAL_ENV' in os.environ:
        raise CLIError("You are already running in a virtual enviroment, yet you want to set a new one up")

    _check_shell()

    heading('Azure CLI Dev Setup')

    # cases for handling legacy install
    if not any([cli_path, ext_repo_path]) or cli_path == "pypi":
        display("WARNING: Installing azdev in legacy mode. Run with atleast -c "
                "to install the latest azdev wihout \"pypi\"\n")
        return _handle_legacy(cli_path, ext_repo_path, ext, deps, time.time())
    if 'CONDA_PREFIX' in os.environ:
        raise CLIError('CONDA virutal enviroments are not supported outside'
                       ' of interactive mode or when -c and -r are provided')
    _validate_input(cli_path, ext_repo_path, set_env, copy, use_global, ext)
    _check_paths(cli_path, ext_repo_path)

    if set_env:
        shell_cmd((const.VENV_CMD if const.IS_WINDOWS else const.VENV_CMD3) + set_env, raise_ex=False)
        azure_path = os.path.join(os.path.abspath(os.getcwd()), set_env)
    else:
        azure_path = os.environ.get(const.VIRTUAL_ENV)

    dot_azure_config = os.path.join(azure_path, '.azure')
    dot_azdev_config = os.path.join(azure_path, '.azdev')

    # clean up venv dirs if they already existed
    # and this is a reinstall/new setup
    if os.path.isdir(dot_azure_config):
        shutil.rmtree(dot_azure_config)
    if os.path.isdir(dot_azdev_config):
        shutil.rmtree(dot_azdev_config)

    global_az_config = os.path.expanduser(os.path.join('~', '.azure'))
    global_azdev_config = os.path.expanduser(os.path.join('~', '.azdev'))
    azure_config_path = os.path.join(dot_azure_config, const.CONFIG_NAME)
    azdev_config_path = os.path.join(dot_azdev_config, const.CONFIG_NAME)

    if os.path.isdir(global_az_config) and copy:
        shutil.copytree(global_az_config, dot_azure_config)
        if os.path.isdir(global_azdev_config):
            shutil.copytree(global_azdev_config, dot_azdev_config)
        else:
            os.mkdir(dot_azdev_config)
            file = open(azdev_config_path, "w")
            file.close()
    elif not use_global and not copy:
        os.mkdir(dot_azure_config)
        os.mkdir(dot_azdev_config)
        file_az, file_dev = open(azure_config_path, "w"), open(azdev_config_path, "w")
        file_az.close()
        file_dev.close()
    elif os.path.isdir(global_az_config):
        dot_azure_config, dot_azdev_config = global_az_config, global_azdev_config
        azure_config_path = os.path.join(dot_azure_config, const.CONFIG_NAME)
    else:
        raise CLIError(
            "Global AZ config is not set up, yet it was specified to be used.")

    # set env vars for get azure config and get azdev config
    os.environ['AZURE_CONFIG_DIR'], os.environ['AZDEV_CONFIG_DIR'] = dot_azure_config, dot_azdev_config
    config = get_azure_config()
    if not config.get(const.CLOUD_SECTION, 'name', None):
        config.set_value(const.CLOUD_SECTION, 'name', const.AZ_CLOUD)
    if ext_repo_path:
        config.set_value(const.EXT_SECTION, const.AZ_DEV_SRC, os.path.abspath(ext_repo_path))
    venv.edit_activate(azure_path, dot_azure_config, dot_azdev_config)
    if cli_path:
        config.set_value(const.CLI_SECTION, const.AZ_DEV_SRC, os.path.abspath(cli_path))
        venv.install_cli(os.path.abspath(cli_path), azure_path)
    config = get_azdev_config()
    config.set_value('ext', 'repo_paths', os.path.abspath(ext_repo_path) if ext_repo_path else '_NONE_')
    config.set_value('cli', 'repo_path', os.path.abspath(cli_path))
    _copy_config_files()
    if ext and ext_repo_path:
        venv.install_extensions(azure_path, ext)

    if not set_env:
        heading("The setup was successful! Please run or re-run the virtual environment activation script.")
    else:
        heading("The setup was successful!")
    return None


def _handle_legacy(cli_path, ext_repo_path, ext, deps, start):
    ext_repo_path = [ext_repo_path] if ext_repo_path else None
    ext_to_install = []
    if not any([cli_path, ext_repo_path, ext]):
        cli_path, ext_repo_path, ext_to_install = _interactive_setup()
    else:
        if cli_path == "pypi":
            cli_path = None
        # otherwise assume programmatic setup
        if cli_path:
            CLI_SENTINEL = 'azure-cli.pyproj'
            if cli_path == Flag:
                cli_path = find_file(CLI_SENTINEL)
            if not cli_path:
                raise CLIError('Unable to locate your CLI repo. Things to check:'
                               '\n    Ensure you have cloned the repo. '
                               '\n    Specify the path explicitly with `-c PATH`. '
                               '\n    If you run with `-c` to autodetect, ensure you are running '
                               'this command from a folder upstream of the repo.')
            if cli_path != 'EDGE':
                cli_path = _check_path(cli_path, CLI_SENTINEL)
            display('Azure CLI:\n    {}\n'.format(cli_path))
        else:
            display('Azure CLI:\n    PyPI\n')

        # must add the necessary repo to add an extension
        if ext and not ext_repo_path:
            raise CLIError('usage error: --repo EXT_REPO [EXT_REPO ...] [--ext EXT_NAME ...]')
        get_azure_config().set_value('extension', 'dev_sources', '')
        if ext_repo_path:
            # add extension repo(s)
            add_extension_repo(ext_repo_path)
            display('Azure CLI extension repos:\n    {}'.format(
                '\n    '.join([os.path.abspath(x) for x in ext_repo_path])))

        if ext == ['*']:
            ext_to_install = [x['path'] for x in list_extensions()]
        elif ext:
            # add extension(s)
            available_extensions = [x['name'] for x in list_extensions()]
            not_found = [x for x in ext if x not in available_extensions]
            if not_found:
                raise CLIError("The following extensions were not found. Ensure you have added "
                               "the repo using `--repo/-r PATH`.\n    {}".format('\n    '.join(not_found)))
            ext_to_install = [x['path'] for x in list_extensions() if x['name'] in ext]

        if ext_to_install:
            display('\nAzure CLI extensions:\n    {}'.format('\n    '.join(ext_to_install)))

    dev_sources = get_azure_config().get('extension', 'dev_sources', None)

    # save data to config files
    config = get_azdev_config()
    config.set_value('ext', 'repo_paths', dev_sources if dev_sources else '_NONE_')
    config.set_value('cli', 'repo_path', cli_path if cli_path else '_NONE_')

    # install packages
    subheading('Installing packages')

    # upgrade to latest pip
    pip_cmd('install --upgrade pip -q', 'Upgrading pip...')
    _install_cli(cli_path, deps=deps)
    if ext_repo_path:
        _install_extensions(ext_to_install)
    _copy_config_files()
    end = time.time()
    elapsed_min = int((end - start) / 60)
    elapsed_sec = int(end - start) % 60
    display('\nElapsed time: {} min {} sec'.format(elapsed_min, elapsed_sec))

    subheading('Finished dev setup!')
