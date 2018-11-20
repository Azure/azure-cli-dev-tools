# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from importlib import import_module
import os
import pkgutil
import glob
import sys

from knack.util import CLIError

from .const import COMMAND_MODULE_PREFIX, EXTENSION_PREFIX
from .display import display


def get_azdev_repo_path():
    """ Return the path to the azdev repo root. 

    :returns: Path (str) to azdev repo.
    """
    here = os.path.dirname(os.path.realpath(__file__))
    while not os.path.exists(os.path.join(here, '.git')):
        here = os.path.dirname(here)
    return here


def get_cli_repo_path():
    """ Return the path to the Azure CLI repo.

    :returns: Path (str) to Azure CLI repo.
    """
    from .config import get_azdev_config
    try:
        return get_azdev_config().get('cli', 'repo_path', None)
    except Exception:
        CLIError('Unable to retrieve CLI repo path from config. Please run `azdev setup`.')


def get_ext_repo_path():
    """ Return the path to the Azure CLI Extensions repo.

    :returns: Path (str) to Azure CLI extensions repo.
    """
    from .config import get_azdev_config
    try:
        return get_azdev_config().get('ext', 'repo_path')
    except Exception:
        CLIError('Unable to retrieve extensions repo path from config. Please run `azdev setup`.')


def find_file(file_name):
    """ Returns the path to a specific file.

    :returns: Path (str) to file or None.
    """
    for path, dirs, files in os.walk(os.getcwd()):
        if file_name in files:
            return path
    return None


def make_dirs(path):
    """ Create directories recursively. """
    import errno
    try:
        os.makedirs(os.path.expanduser(path))
    except OSError as exc:  # Python <= 2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_command_module_paths(include_prefix=False):
    """ Returns a list of command module names and paths.

    :param include_prefix: (bool) preserve the 'azure-cli-' prefix in module names.
    :returns: [(str, str)] List of (name, path) tuples.
    """
    cli_path = get_cli_repo_path()
    glob_pattern = os.path.normcase(os.path.join('src', 'command_modules', '{}*'.format(COMMAND_MODULE_PREFIX), 'setup.py'))
    paths = []
    for path in glob.glob(os.path.join(cli_path, glob_pattern)):
        folder = os.path.dirname(path)
        name = os.path.basename(folder)
        if not include_prefix:
            name = name[len(COMMAND_MODULE_PREFIX):]
        paths.append((name, folder))
    return paths


def get_core_module_paths(include_prefix=False):
    """ Returns a list of core module names and paths.

    :param include_prefix: (bool) preserve the 'azure-cli-' prefix in module names.
    :returns: [(str, str)] List of (name, path) tuples.
    """
    cli_path = get_cli_repo_path()
    paths = []
    for path in glob.glob(cli_path + os.path.normcase('/src/*/setup.py')):
        name = os.path.basename(os.path.dirname(path))
        if not include_prefix:
            name = name[len(COMMAND_MODULE_PREFIX):] or '__main__'
        folder = os.path.join(os.path.dirname(path))
        paths.append((name, folder))
    return paths


def get_extension_paths():
    """ Returns a list of extension names and paths.

    :returns: [(str, str)] List of (name, path) tuples.
    """
    ext_path = get_ext_repo_path()
    glob_pattern = os.path.normcase(os.path.join('src', '*', '*.egg-info'))
    paths = []
    for path in glob.glob(os.path.join(ext_path, glob_pattern)):
        folder = os.path.dirname(path)
        name = os.path.basename(folder)
        paths.append((name, folder))
    return paths


def filter_module_paths(paths, filter):
    """ Filter command module and extension paths.

    :param paths: [(str, str)] List of (name, path) tuples.
    :param filter: [str] List of command module or extension names to return, or None to return all.
    """
    if not filter:
        return paths

    if isinstance(filter, str):
        filter = [filter]

    filtered = []
    for name, path in paths:
        if name in filter:
            filtered.append((name, path))
            filter.remove(name)
    if filter:
        raise CLIError('unrecognized names: {}'.format(' '.join(filter)))
    return filtered
