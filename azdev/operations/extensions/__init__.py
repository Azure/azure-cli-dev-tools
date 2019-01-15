# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from collections import OrderedDict
import os
import shutil

from knack.log import get_logger
from knack.util import CLIError

from azdev.utilities import (
    pip_cmd, display, get_ext_repo_paths, find_files, get_azure_config, get_env_config, require_azure_cli)

logger = get_logger(__name__)


def add_extension(extensions):

    require_azure_cli()

    ext_paths = get_ext_repo_paths()
    all_extensions = find_files(ext_paths, 'setup.py')

    paths_to_add = []
    for path in all_extensions:
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
            raise result.error  # pylint: disable=raising-bad-type


def remove_extension(extensions):

    require_azure_cli()

    ext_paths = get_ext_repo_paths()
    installed_paths = find_files(ext_paths, '*.*-info')
    paths_to_remove = []
    names_to_remove = []
    for path in installed_paths:
        folder = os.path.dirname(path)
        long_name = os.path.basename(folder)
        if long_name in extensions:
            paths_to_remove.append(folder)
            names_to_remove.append(long_name)
            extensions.remove(long_name)
    # raise error if any extension not installed
    if extensions:
        raise CLIError('extension(s) not installed: {}'.format(' '.join(extensions)))

    # removes any links that may have been added to site-packages.
    for ext in names_to_remove:
        pip_cmd('uninstall {} -y'.format(ext))

    for path in paths_to_remove:
        for d in os.listdir(path):
            # delete the egg-info and dist-info folders to make the extension invisible to the CLI and azdev
            if d.endswith('egg-info') or d.endswith('dist-info'):
                path_to_remove = os.path.join(path, d)
                display("Removing '{}'...".format(path_to_remove))
                shutil.rmtree(path_to_remove)


def _get_installed_dev_extensions(dev_sources):
    from glob import glob
    installed = []

    def _collect(path, depth=0, max_depth=3):
        if not os.path.isdir(path) or depth == max_depth or os.path.split(path)[-1].startswith('.'):
            return
        pattern = os.path.join(path, '*.egg-info')
        match = glob(pattern)
        if match:
            ext_path = os.path.dirname(match[0])
            ext_name = os.path.split(ext_path)[-1]
            installed.append({'name': ext_name, 'path': ext_path})
        else:
            for item in os.listdir(path):
                _collect(os.path.join(path, item), depth + 1, max_depth)
    for source in dev_sources:
        _collect(source)
    return installed


def list_extensions():

    require_azure_cli()

    azure_config = get_azure_config()
    dev_sources = azure_config.get('extension', 'dev_sources', None)
    dev_sources = dev_sources.split(',') if dev_sources else []

    installed = _get_installed_dev_extensions(dev_sources)
    installed_names = [x['name'] for x in installed]
    results = []

    for ext_path in find_files(dev_sources, 'setup.py'):
        folder = os.path.dirname(ext_path)
        long_name = os.path.basename(folder)
        if long_name not in installed_names:
            results.append({'name': long_name, 'inst': '', 'path': folder})
        else:
            results.append({'name': long_name, 'inst': 'Y', 'path': folder})
    return results


def _get_sha256sum(a_file):
    import hashlib
    sha256 = hashlib.sha256()
    with open(a_file, 'rb') as f:
        sha256.update(f.read())
    return sha256.hexdigest()


def add_extension_repo(repos):

    require_azure_cli()

    from azdev.operations.setup import _check_repo
    az_config = get_azure_config()
    env_config = get_env_config()
    dev_sources = az_config.get('extension', 'dev_sources', None)
    dev_sources = dev_sources.split(',') if dev_sources else []
    for repo in repos:
        repo = os.path.abspath(repo)
        _check_repo(repo)
        if repo not in dev_sources:
            dev_sources.append(repo)
    az_config.set_value('extension', 'dev_sources', ','.join(dev_sources))
    env_config.set_value('ext', 'repo_paths', ','.join(dev_sources))

    return list_extension_repos()


def remove_extension_repo(repos):

    require_azure_cli()

    az_config = get_azure_config()
    env_config = get_env_config()
    dev_sources = az_config.get('extension', 'dev_sources', None)
    dev_sources = dev_sources.split(',') if dev_sources else []
    for repo in repos:
        try:
            dev_sources.remove(os.path.abspath(repo))
        except ValueError:
            logger.warning("Repo '%s' was not found in the list of repositories to search.", os.path.abspath(repo))
    az_config.set_value('extension', 'dev_sources', ','.join(dev_sources))
    env_config.set_value('ext', 'repo_paths', ','.join(dev_sources))
    return list_extension_repos()


def list_extension_repos():

    require_azure_cli()

    az_config = get_azure_config()
    dev_sources = az_config.get('extension', 'dev_sources', None)
    return dev_sources.split(',') if dev_sources else dev_sources


def update_extension_index(extension):
    import json
    import re
    import tempfile

    from .util import get_ext_metadata, get_whl_from_url

    require_azure_cli()

    ext_repos = get_ext_repo_paths()
    index_path = next((x for x in find_files(ext_repos, 'index.json') if 'azure-cli-extensions' in x), None)
    if not index_path:
        raise CLIError("Unable to find 'index.json' in your extension repos. Have "
                       "you cloned 'azure-cli-extensions' and added it to you repo "
                       "sources with `azdev extension repo add`?")

    NAME_REGEX = r'.*/([^/]*)-\d+.\d+.\d+'

    # Get extension WHL from URL
    if not extension.endswith('.whl') or not extension.startswith('https:'):
        raise ValueError('usage error: only URL to a WHL file currently supported.')

    # TODO: extend to consider other options
    ext_path = extension

    # Extract the extension name
    try:
        extension_name = re.findall(NAME_REGEX, ext_path)[0]
        extension_name = extension_name.replace('_', '-')
    except IndexError:
        raise ValueError('unable to parse extension name')

    extensions_dir = tempfile.mkdtemp()
    ext_dir = tempfile.mkdtemp(dir=extensions_dir)
    whl_cache_dir = tempfile.mkdtemp()
    whl_cache = {}
    ext_file = get_whl_from_url(ext_path, extension_name, whl_cache_dir, whl_cache)

    with open(index_path, 'r') as infile:
        curr_index = json.loads(infile.read())

    entry = {
        'downloadUrl': ext_path,
        'sha256Digest': _get_sha256sum(ext_file),
        'filename': ext_path.split('/')[-1],
        'metadata': get_ext_metadata(ext_dir, ext_file, extension_name)
    }

    if extension_name not in curr_index['extensions'].keys():
        logger.info("Adding '%s' to index...", extension_name)
        curr_index['extensions'][extension_name] = [entry]
    else:
        logger.info("Updating '%s' in index...", extension_name)
        curr_index['extensions'][extension_name].append(entry)

    # update index and write back to file
    with open(os.path.join(index_path), 'w') as outfile:
        outfile.write(json.dumps(curr_index, indent=4, sort_keys=True))
