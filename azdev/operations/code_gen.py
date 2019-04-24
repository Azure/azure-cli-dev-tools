# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from __future__ import print_function

import os
import re
import sys

from knack.prompting import prompt_y_n
from knack.util import CLIError


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
                  sdk_client=None):
    from jinja2 import Environment, PackageLoader
    from azdev.utilities import COMMAND_MODULE_PREFIX, get_cli_repo_path

    if mod_name.startswith(COMMAND_MODULE_PREFIX):
        mod_name = mod_name[len(COMMAND_MODULE_PREFIX):]

    display_name = display_name or mod_name.capitalize()

    kwargs = {
        'name': mod_name,
        'mod_path': 'azure.cli.command_modules.{}'.format(mod_name),
        'display_name': display_name,
        'loader_name': '{}CommandsLoader'.format(display_name)
    }

    if required_sdk or sdk_client:
        version_regex = r'(?P<name>[a-zA-Z-]+)(?P<op>[~<>=]*)(?P<version>[\d.]*)'
        regex = re.compile(version_regex)
        version_comps = regex.match(required_sdk)
        sdk_kwargs = version_comps.groupdict()
        kwargs.update({
            'sdk_path': sdk_kwargs['name'].replace('-', '.'),
            'sdk_client': sdk_client,
            'dependencies': [sdk_kwargs]
        })

    cli_path = get_cli_repo_path()
    package_name = 'azure-cli-{}'.format(mod_name.replace('_', '-'))
    new_module_path = os.path.join(cli_path, 'src', 'command_modules', package_name)
    if os.path.isdir(new_module_path):
        if not prompt_y_n("'{}' already exists. Overwrite?".format(package_name), default='n'):
            return

    # create folder tree
    _ensure_dir(os.path.join(new_module_path, 'azure', 'cli', 'command_modules', mod_name, 'tests', 'latest'))
    env = Environment(loader=PackageLoader('azdev', 'mod_templates'))

    # generate code for root level
    dest_path = new_module_path
    root_files = [
        'azure_bdist_wheel.py',
        'HISTORY.rst',
        'MANIFEST.in',
        'README.rst',
        'setup.cfg',
        'setup.py'
    ]
    _generate_files(env, kwargs, root_files, dest_path)

    dest_path = os.path.join(dest_path, 'azure')
    pkg_init = {'name': '__init__.py', 'template': 'pkg_declare__init__.py'}
    _generate_files(env, kwargs, pkg_init, dest_path)

    dest_path = os.path.join(dest_path, 'cli')
    _generate_files(env, kwargs, pkg_init, dest_path)

    dest_path = os.path.join(dest_path, 'command_modules')
    _generate_files(env, kwargs, pkg_init, dest_path)

    dest_path = os.path.join(dest_path, mod_name)
    module_files = [
        {'name': '__init__.py', 'template': 'module__init__.py'},
        '_client_factory.py',
        '_help.py',
        '_params.py',
        '_validators.py',
        'commands.py',
        'custom.py'
    ]
    _generate_files(env, kwargs, module_files, dest_path)

    dest_path = os.path.join(dest_path, 'tests')
    blank_init = {'name': '__init__.py', 'template': 'blank__init__.py'}
    _generate_files(env, kwargs, blank_init, dest_path)

    dest_path = os.path.join(dest_path, 'latest')
    test_files = [
        blank_init,
        {'name': 'test_{}_scenario.py'.format(mod_name), 'template': 'test_service_scenario.py'}
    ]
    _generate_files(env, kwargs, test_files, dest_path)

    # TODO: add module to the azure-cli's "setup.py" file
    # TODO: add module to doc source map
    # TODO: add module to Github code owners file

    print('WOOT!  Module generated! Re-run `azdev setup` to install!')
