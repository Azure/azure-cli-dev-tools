# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from __future__ import print_function

import json
import os
import re
from subprocess import CalledProcessError

from knack.log import get_logger
from knack.prompting import prompt_y_n
from knack.util import CLIError

from azdev.utilities import (
    pip_cmd, display, heading, COMMAND_MODULE_PREFIX, EXTENSION_PREFIX, get_cli_repo_path, get_ext_repo_paths,
    find_files)

logger = get_logger(__name__)


def _ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def _generate_files(env, generation_kwargs, file_list, dest_path):

    # allow sending a single item
    if not isinstance(file_list, list):
        file_list = [file_list]

    for metadata in file_list:
        # shortcut if source and dest filenames are the same
        if isinstance(metadata, str):
            metadata = {'name': metadata, 'template': metadata}

        with open(os.path.join(dest_path, metadata['name']), 'w') as f:
            f.write(env.get_template(metadata['template']).render(**generation_kwargs))


def create_module(mod_name='test', display_name=None, display_name_plural=None, required_sdk=None,
                  client_name=None, operation_name=None, sdk_property=None, not_preview=False, github_alias=None):
    repo_path = os.path.join(get_cli_repo_path(), 'src', 'command_modules')
    _create_package(COMMAND_MODULE_PREFIX, repo_path, False, mod_name, display_name, display_name_plural,
                    required_sdk, client_name, operation_name, sdk_property, not_preview,
                    github_alias)
    _add_to_codeowners(get_cli_repo_path(), COMMAND_MODULE_PREFIX, mod_name, github_alias)
    _add_to_setup_py(get_cli_repo_path(), mod_name)
    _add_to_doc_map(get_cli_repo_path(), mod_name)

    display('\nCreation of {prefix}{mod} successful! Run `az {mod} -h` to get started!'.format(
        prefix=COMMAND_MODULE_PREFIX, mod=mod_name))


def create_extension(ext_name='test', repo_name='azure-cli-extensions',
                     display_name=None, display_name_plural=None,
                     required_sdk=None, client_name=None, operation_name=None, sdk_property=None,
                     not_preview=False, github_alias=None):
    repo_path = None
    repo_paths = get_ext_repo_paths()
    repo_path = next((x for x in repo_paths if x.endswith(repo_name)), None)

    if not repo_path:
        raise CLIError('Unable to find `{}` repo. Have you cloned it and added '
                       'with `azdev extension repo add`?'.format(repo_name))

    _create_package(EXTENSION_PREFIX, os.path.join(repo_path, 'src'), True, ext_name, display_name,
                    display_name_plural, required_sdk, client_name, operation_name, sdk_property, not_preview,
                    github_alias)
    _add_to_codeowners(repo_path, EXTENSION_PREFIX, ext_name, github_alias)

    display('\nCreation of {prefix}{mod} successful! Run `az {mod} -h` to get started!'.format(
        prefix=EXTENSION_PREFIX, mod=ext_name))


def _download_vendored_sdk(required_sdk, path):
    import shutil
    import zipfile

    path_regex = re.compile(r'.*((\s*.*downloaded\s)|(\s*.*saved\s))(?P<path>.*\.whl)', re.IGNORECASE | re.S)

    # download and extract the required SDK to the vendored_sdks folder
    downloaded_path = None
    if required_sdk:
        display('Downloading {}...'.format(required_sdk))
        vendored_sdks_path = path
        result = pip_cmd('download {} --no-deps -d {}'.format(required_sdk, vendored_sdks_path)).result
        try:
            result = result.decode('utf-8')
        except AttributeError:
            pass
        for line in result.splitlines():
            try:
                downloaded_path = path_regex.match(line).group('path')
            except AttributeError:
                continue
            break
        if not downloaded_path:
            raise CLIError('Unable to download: {}'.format(required_sdk))

        # extract the WHL file
        with zipfile.ZipFile(str(downloaded_path), 'r') as z:
            z.extractall(vendored_sdks_path)

        # remove the WHL file
        try:
            os.remove(downloaded_path)
        except OSError:
            logger.warning('Unable to remove %s. Trying manually deleting.', downloaded_path)

        try:
            client_location = find_files(vendored_sdks_path, 'version.py')[0]
        except KeyError:
            raise CLIError('Unable to find client files.')

        # copy the client files and folders to the root of vendored_sdks for easier access
        client_dir = os.path.dirname(client_location)
        for item in os.listdir(client_dir):
            src = os.path.join(client_dir, item)
            dest = os.path.join(vendored_sdks_path, item)
            shutil.move(src, dest)
        try:
            os.remove(os.path.join(vendored_sdks_path, 'azure'))
        except OSError:
            logger.warning('Unable to remove %s. Try manually deleting.', os.path.join(vendored_sdks_path, 'azure'))


def _add_to_codeowners(repo_path, prefix, name, github_alias):
    # add the user Github alias to the CODEOWNERS file for new packages
    if not github_alias:
        from knack.prompting import prompt
        display('\nWhat is the Github alias of the person responsible for maintaining this package?')
        while not github_alias:
            github_alias = prompt('Alias: ')

    # accept a raw alias or @alias
    github_alias = '@{}'.format(github_alias) if not github_alias.startswith('@') else github_alias
    try:
        codeowners = find_files(repo_path, 'CODEOWNERS')[0]
    except IndexError:
        raise CLIError('unexpected error: unable to find CODEOWNERS file.')

    if prefix == COMMAND_MODULE_PREFIX:
        new_line = '/src/command_modules/{}{}/ {}'.format(prefix, name, github_alias)
    else:
        new_line = '/src/{}{}/ {}'.format(prefix, name, github_alias)

    with open(codeowners, 'a') as f:
        f.write(new_line)
        f.write('\n')


def _add_to_setup_py(repo_path, name):
    setup_file = find_files(repo_path, 'setup.py')
    print(setup_file)


def _add_to_doc_map(repo_path, name):
    try:
        doc_source_file = find_files(repo_path, 'doc_source_map.json')[0]
    except IndexError:
        raise CLIError('unexpected error: unable to find doc_source_map.json file.')
    doc_source = None
    with open(doc_source_file, 'r') as f:
        doc_source = json.loads(f.read())

    # TODO: Fix format!
    doc_source[name] = 'src/command_modules/azure-cli-{0}/azure/cli/command_modules/{0}/_help.py'.format(name)
    with open(doc_source_file, 'w') as f:
        f.write(json.dumps(doc_source))


# pylint: disable=too-many-locals, too-many-statements
def _create_package(prefix, repo_path, is_ext, name='test', display_name=None, display_name_plural=None,
                    required_sdk=None, client_name=None, operation_name=None, sdk_property=None,
                    not_preview=False, github_alias=None):
    from jinja2 import Environment, PackageLoader

    if name.startswith(prefix):
        name = name[len(prefix):]

    heading('Create CLI {}: {}{}'.format('Extension' if is_ext else 'Module', prefix, name))

    # package_name is how the item should show up in `pip list`
    package_name = '{}{}'.format(prefix, name.replace('_', '-')) if not is_ext else name
    display_name = display_name or name.capitalize()

    kwargs = {
        'name': name,
        'mod_path': '{}{}'.format(prefix, name) if is_ext else 'azure.cli.command_modules.{}'.format(name),
        'display_name': display_name,
        'display_name_plural': display_name_plural or '{}s'.format(display_name),
        'loader_name': '{}CommandsLoader'.format(name.capitalize()),
        'pkg_name': package_name,
        'ext_long_name': '{}{}'.format(prefix, name) if is_ext else None,
        'is_ext': is_ext,
        'is_preview': not not_preview
    }

    new_package_path = os.path.join(repo_path, package_name)
    if os.path.isdir(new_package_path):
        if not prompt_y_n(
                "{} '{}' already exists. Overwrite?".format('Extension' if is_ext else 'Module', package_name),
                default='n'):
            return

    ext_folder = '{}{}'.format(prefix, name) if is_ext else None

    # create folder tree
    if is_ext:
        _ensure_dir(os.path.join(new_package_path, ext_folder, 'tests', 'latest'))
        _ensure_dir(os.path.join(new_package_path, ext_folder, 'vendored_sdks'))
    else:
        _ensure_dir(os.path.join(new_package_path, 'azure', 'cli', 'command_modules', name, 'tests', 'latest'))
    env = Environment(loader=PackageLoader('azdev', 'mod_templates'))

    # determine dependencies
    dependencies = []
    if is_ext:

        dependencies.append("'azure-cli-core'")
        _download_vendored_sdk(
            required_sdk,
            path=os.path.join(new_package_path, ext_folder, 'vendored_sdks')
        )
        kwargs.update({
            'sdk_path': required_sdk and '{}{}.vendored_sdks'.format(prefix, package_name),
            'client_name': client_name,
            'operation_name': operation_name,
            'sdk_property': sdk_property or '{}_name'.format(name)
        })
    else:
        if required_sdk:
            version_regex = r'(?P<name>[a-zA-Z-]+)(?P<op>[~<>=]*)(?P<version>[\d.]*)'
            version_comps = re.compile(version_regex).match(required_sdk)
            sdk_kwargs = version_comps.groupdict()
            kwargs.update({
                'sdk_path': sdk_kwargs['name'].replace('-', '.'),
                'client_name': client_name,
                'operation_name': operation_name,
            })
            dependencies.append("'{}'".format(required_sdk))
        else:
            dependencies.append('# TODO: azure-mgmt-<NAME>==<VERSION>')
        kwargs.update({'sdk_property': sdk_property or '{}_name'.format(name)})

    kwargs['dependencies'] = dependencies

    # generate code for root level
    dest_path = new_package_path
    root_files = [
        'HISTORY.rst',
        'MANIFEST.in',
        'README.rst',
        'setup.cfg',
        'setup.py'
    ]
    if not is_ext:
        root_files.append('azure_bdist_wheel.py')
    _generate_files(env, kwargs, root_files, dest_path)

    if not is_ext:
        dest_path = os.path.join(dest_path, 'azure')
        pkg_init = {'name': '__init__.py', 'template': 'pkg_declare__init__.py'}
        _generate_files(env, kwargs, pkg_init, dest_path)

        dest_path = os.path.join(dest_path, 'cli')
        _generate_files(env, kwargs, pkg_init, dest_path)

        dest_path = os.path.join(dest_path, 'command_modules')
        _generate_files(env, kwargs, pkg_init, dest_path)

    dest_path = os.path.join(dest_path, ext_folder if is_ext else name)
    module_files = [
        {'name': '__init__.py', 'template': 'module__init__.py'},
        '_client_factory.py',
        '_help.py',
        '_params.py',
        '_validators.py',
        'commands.py',
        'custom.py'
    ]
    if is_ext:
        module_files.append('azext_metadata.json')
    _generate_files(env, kwargs, module_files, dest_path)

    dest_path = os.path.join(dest_path, 'tests')
    blank_init = {'name': '__init__.py', 'template': 'blank__init__.py'}
    _generate_files(env, kwargs, blank_init, dest_path)

    dest_path = os.path.join(dest_path, 'latest')
    test_files = [
        blank_init,
        {'name': 'test_{}_scenario.py'.format(name), 'template': 'test_service_scenario.py'}
    ]
    _generate_files(env, kwargs, test_files, dest_path)

    if not is_ext:
        # install the newly created module
        try:
            result = pip_cmd("install -q -e {}".format(new_package_path), "Installing `{}{}`...".format(prefix, name))
            if 'ERROR' in str(result.result):
                raise CLIError('Failed to install. {}'.format(str(result.result)))
        except CalledProcessError as err:
            # exit code is not zero
            raise CLIError("Failed to install. Error message: {}".format(err.output))
        finally:
            # Ensure that the site package's azure/__init__.py has the old style namespace
            # package declaration by installing the old namespace package
            pip_cmd("install -q -I azure-nspkg==1.0.0", "Installing `azure-nspkg`...")
            pip_cmd("install -q -I azure-mgmt-nspkg==1.0.0", "Installing `azure-mgmt-nspkg`...")
    else:
        result = pip_cmd('install -e {}'.format(new_package_path), "Installing `{}{}`...".format(prefix, name))
        if result.error:
            raise result.error  # pylint: disable=raising-bad-type
