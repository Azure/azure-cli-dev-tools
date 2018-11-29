# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from collections import OrderedDict
from glob import glob
import os
import shutil

from azdev.utilities import pip_cmd, display, get_ext_repo_path

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


def add_extension(extensions):
    ext_path = get_ext_repo_path()
    all_ext_pattern = os.path.normcase(os.path.join(ext_path, 'src', '*', 'setup.py'))
    all_extensions = glob(all_ext_pattern)

    paths_to_add = []
    for path in all_extensions:
        target_path = None
        folder = os.path.dirname(path)
        long_name = os.path.basename(folder)
        if long_name in extensions:
            paths_to_add.append(folder)
            extensions.remove(long_name)
    # raise error if any extension wasn't found
    if extensions:
        raise CLIError('extension(s) not found: {}'.format(' '.join(extensions)))

    for path in paths_to_add:
        result = pip_cmd('install -e {}'.format(path), "Adding extension '{}'...".format(path))
        if result.error:
            raise result.error


def remove_extension(extensions):
    ext_path = get_ext_repo_path()
    installed_paths = []
    installed_paths.extend(glob(os.path.normcase(os.path.join(ext_path, 'src', '*', '*.*-info'))))
    paths_to_remove = []
    for path in installed_paths:
        target_path = None
        folder = os.path.dirname(path)
        long_name = os.path.basename(folder)
        if long_name in extensions:
            paths_to_remove.append(folder)
            extensions.remove(long_name)
    # raise error if any extension not installed
    if extensions:
        raise CLIError('extension(s) not installed: {}'.format(' '.join(extensions)))

    for path in paths_to_remove:
        for d in os.listdir(path):
            # delete the egg-info and dist-info folders to make the extension invisible to the CLI and azdev
            if d.endswith('egg-info') or d.endswith('dist-info'):
                path_to_remove = os.path.join(path, d)
                display("Removing '{}'...".format(path_to_remove))
                shutil.rmtree(path_to_remove)


def list_extensions():
    ext_path = get_ext_repo_path()
    all_ext_pattern = os.path.normcase(os.path.join(ext_path, 'src', '*', 'setup.py'))
    installed_paths = []
    installed_paths.extend(glob(os.path.normcase(os.path.join(ext_path, 'src', '*', '*.*-info'))))

    results = []
    installed = []
    for path in installed_paths:
        folder = os.path.dirname(path)
        long_name = os.path.basename(folder)
        results.append({'name': '{} (INSTALLED)'.format(long_name), 'path': folder})
        installed.append(long_name)

    for path in glob(all_ext_pattern):
        folder = os.path.dirname(path)
        long_name = os.path.basename(folder)
        if long_name not in installed:
            results.append({'name': long_name, 'path': folder})
    return results
