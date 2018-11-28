# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from importlib import import_module
import os
import pkgutil
from glob import glob
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


def get_path_table(filter=None):
    """ Gets a table which contains the long and short names of different modules and extensions and the path to them. The structure looks like:

    {
        'core': {
            NAME: PATH,
            ...
        },
        'mod': {
            NAME: PATH,
            ...
        },
        'ext': {
            NAME: PATH,
            ...
        }
    }
    """

    # determine whether the call will filter or return all
    if isinstance(filter, str):
        filter = [filter]
    get_all = not filter

    table = {}
    cli_path = get_cli_repo_path()
    ext_path = get_ext_repo_path()
    module_pattern = os.path.normcase(os.path.join(cli_path, 'src', 'command_modules', '{}*'.format(COMMAND_MODULE_PREFIX), 'setup.py'))
    core_pattern = os.path.normcase(os.path.join(cli_path, 'src', '*', 'setup.py'))
    ext_pattern = os.path.normcase(os.path.join(ext_path, 'src', '*', '*.egg-info'))

    def _update_table(pattern, key):
        if key not in table:
            table[key] = {}
        folder = None
        long_name = None
        short_name = None
        for path in glob(pattern):
            folder = os.path.dirname(path)
            long_name = os.path.basename(folder)
            # determine short-names
            if key == 'ext':
                for item in os.listdir(folder):
                    if item.startswith(EXTENSION_PREFIX):
                        short_name = item
                        break
            else:
                short_name = long_name[len(COMMAND_MODULE_PREFIX):] or '__main__'

            if get_all:
                table[key][long_name] = folder
                continue
            elif not filter:
                # nothing left to filter
                return
            else:
                # check and update filter
                if short_name in filter:
                    filter.remove(short_name)
                    table[key][short_name] = folder
                if long_name in filter:
                    # long name takes precedence to ensure path doesn't appear twice
                    filter.remove(long_name)
                    table[key].pop(short_name)
                    table[key][long_name] = folder

    _update_table(module_pattern, 'mod')
    _update_table(core_pattern, 'core')
    _update_table(ext_pattern, 'ext')

    if filter:
        raise CLIError('unrecognized names: {}'.format(' '.join(filter)))

    return table


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
