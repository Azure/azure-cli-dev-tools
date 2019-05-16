# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from __future__ import print_function

import os
import re
from subprocess import CalledProcessError
import sys

from knack.prompting import prompt_y_n
from knack.util import CLIError

from azdev.utilities import (
    pip_cmd, display, heading, COMMAND_MODULE_PREFIX, EXTENSION_PREFIX, get_cli_repo_path, get_ext_repo_paths)


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


def create_module(mod_name='test', display_name=None, required_sdk=None,
                  client_name=None, operation_name=None):
    repo_path = os.path.join(get_cli_repo_path(), 'src', 'command_modules')
    _create_package(COMMAND_MODULE_PREFIX, repo_path, False, mod_name, display_name, required_sdk,
                    client_name, operation_name)

def create_extension(ext_name='test', repo_name=None, display_name=None, required_sdk=None,
                     client_name=None, operation_name=None):
    repo_paths = get_ext_repo_paths()
    repo_path = next((x for x in repo_paths if x.endswith('azure-cli-extensions')), None)
    if not repo_path:
        raise CLIError('Unable to find `azure-cli-extension` repo. Have you cloned it and added '
                       'with `azdev extension repo add`?')
    repo_path = os.path.join(repo_path, 'src')
    _create_package(EXTENSION_PREFIX, repo_path, True, ext_name, display_name, required_sdk,
                    client_name, operation_name)


def _create_package(prefix, repo_path, is_ext, name='test', display_name=None, required_sdk=None,
                    client_name=None, operation_name=None):
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
        'loader_name': '{}CommandsLoader'.format(name.capitalize()),
        'pkg_name': package_name,
        'ext_long_name': '{}{}'.format(prefix, name) if is_ext else None,
        'is_ext': is_ext
    }

    if required_sdk:
        version_regex = r'(?P<name>[a-zA-Z-]+)(?P<op>[~<>=]*)(?P<version>[\d.]*)'
        regex = re.compile(version_regex)
        version_comps = regex.match(required_sdk)
        sdk_kwargs = version_comps.groupdict()
        kwargs.update({
            'sdk_path': sdk_kwargs['name'].replace('-', '.'),
            'client_name': client_name,
            'operation_name': operation_name,
            'dependencies': [sdk_kwargs]
        })

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
            pip_cmd("install -q -e {}".format(new_package_path), "Installing `{}{}`...".format(prefix, name))
        except CalledProcessError as err:
            # exit code is not zero
            raise CLIError("Failed to install. Error message: {}".format(err.output))
        finally:
            # Ensure that the site package's azure/__init__.py has the old style namespace
            # package declaration by installing the old namespace package
            pip_cmd("install -q -I azure-nspkg==1.0.0", "Installing `azure-nspkg`...")
            pip_cmd("install -q -I azure-mgmt-nspkg==1.0.0", "Installing `azure-mgmt-nspkg`...")
    else:
        # TODO: Install extension
        result = pip_cmd('install -e {}'.format(new_package_path), "Installing `{}{}`...".format(prefix, name))
        if result.error:
            raise result.error  # pylint: disable=raising-bad-type


    if not is_ext:
        # TODO: add module to the azure-cli's "setup.py" file
        # TODO: add module to doc source map
        pass

    # TODO: add module to Github code owners file

    display('\nCreation of {prefix}{mod} successful! Run `az {mod} -h` to get started!'.format(prefix=prefix, mod=name))
