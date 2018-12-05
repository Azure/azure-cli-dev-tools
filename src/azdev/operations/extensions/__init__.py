# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict
import os
import shutil

from azdev.utilities import pip_cmd, display, get_ext_repo_path, find_files

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


def add_extension(extensions):
    ext_path = get_ext_repo_path()
    all_extensions = find_files(ext_path, 'setup.py')

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
    installed_paths = find_files(ext_path, '*.*-info')
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
    installed_paths = find_files(ext_path, '*.*-info')

    results = []
    installed = []
    for path in installed_paths:
        folder = os.path.dirname(path)
        long_name = os.path.basename(folder)
        results.append({'name': '{} (INSTALLED)'.format(long_name), 'path': folder})
        installed.append(long_name)

    for path in find_files(ext_path, 'setup.py'):
        folder = os.path.dirname(path)
        long_name = os.path.basename(folder)
        if long_name not in installed:
            results.append({'name': long_name, 'path': folder})
    return results


def _get_sha256sum(a_file):
    import hashlib
    sha256 = hashlib.sha256()
    with open(a_file, 'rb') as f:
        sha256.update(f.read())
    return sha256.hexdigest()


def update_extension_index(extension):
    import json
    import re
    import tempfile

    from .util import get_ext_metadata, get_whl_from_url

    NAME_REGEX = r'.*/([^/]*)-\d+.\d+.\d+'

    ext_path = get_ext_repo_path()

    # Get extension WHL from URL
    if not extension.endswith('.whl') or not extension.startswith('https:'):
        raise ValueError('usage error: only URL to a WHL file currently supported.')

    # Extract the extension name
    try:
        extension_name = re.findall(NAME_REGEX, extension)[0]
        extension_name = extension_name.replace('_', '-')
    except IndexError:
        raise ValueError('unable to parse extension name')

    extensions_dir = tempfile.mkdtemp()
    ext_dir = tempfile.mkdtemp(dir=extensions_dir)
    whl_cache_dir = tempfile.mkdtemp()
    whl_cache = {}
    ext_file = get_whl_from_url(whl_path, extension_name, whl_cache_dir, whl_cache)

    with open(os.join(ext_path, 'src', 'index.json'), 'r') as infile:
        curr_index = json.loads(infile.read())

    try:
        entry = curr_index['extensions'][extension_name]
    except IndexError:
        raise ValueError('{} not found in index.json'.format(extension_name))

    entry[0]['downloadUrl'] = whl_path
    entry[0]['sha256Digest'] = _get_sha256sum(ext_file)
    entry[0]['filename'] = whl_path.split('/')[-1]
    entry[0]['metadata'] = get_ext_metadata(ext_dir, ext_file, extension_name)

    # update index and write back to file
    curr_index['extensions'][extension_name] = entry
    with open(os.join(ext_path, 'src', 'index.json'), 'w') as outfile:
        outfile.write(json.dumps(curr_index, indent=4, sort_keys=True))
