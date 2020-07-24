# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from __future__ import print_function

import json
import os
import re
import subprocess

from knack.log import get_logger
from knack.prompting import prompt_y_n, prompt
from knack.util import CLIError

import azdev.utilities.const as const

from azdev.utilities import (
    pip_cmd, shell_cmd, display, heading, COMMAND_MODULE_PREFIX, EXTENSION_PREFIX, get_cli_repo_path,
    get_ext_repo_paths, find_files, require_virtual_env)

from urllib import request, error


logger = get_logger(__name__)

_MODULE_ROOT_PATH = os.path.join('src', 'azure-cli', 'azure', 'cli', 'command_modules')


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
                  client_name=None, operation_name=None, sdk_property=None, not_preview=False, github_alias=None,
                  local_sdk=None):
    repo_path = os.path.join(get_cli_repo_path(), _MODULE_ROOT_PATH)
    _create_package('', repo_path, False, mod_name, display_name, display_name_plural,
                    required_sdk, client_name, operation_name, sdk_property, not_preview, local_sdk)
    _add_to_codeowners(get_cli_repo_path(), '', mod_name, github_alias)
    _add_to_doc_map(get_cli_repo_path(), mod_name)

    _display_success_message(COMMAND_MODULE_PREFIX + mod_name, mod_name)


def create_extension(ext_name, azure_rest_api_specs=const.GITHUB_SWAGGER_REPO_URL, branch=None, use=None):
    if not azure_rest_api_specs.startswith('http') and branch:
        raise CLIError('Cannot specify azure-rest-api-specs repo branch when using local one.')
    if not branch:
        branch = json.load(request.urlopen(const.GITHUB_API_SWAGGER_REPO_URL)).get('default_branch')
    require_virtual_env()
    repo_paths = get_ext_repo_paths()
    repo_path = next(
        (x for x in repo_paths if x.endswith(const.EXT_REPO_NAME) or x.endswith(const.EXT_REPO_NAME + '\\')), None)
    if not repo_path:
        raise CLIError('Unable to find `{}` repo. Have you cloned it and added '
                       'with `azdev extension repo add`?'.format(const.EXT_REPO_NAME))
    if not os.path.isdir(repo_path):
        raise CLIError("Invalid path {} in .azure config.".format(repo_path))
    swagger_readme_file_path = _get_swagger_readme_file_path(ext_name, azure_rest_api_specs, branch)
    _generate_extension(ext_name, repo_path, swagger_readme_file_path, use)
    _add_extension(ext_name, repo_path)

    _display_success_message(ext_name, ext_name)


def _display_success_message(package_name, group_name):
    heading('Creation of {} successful!'.format(package_name))
    display('Getting started:')
    display('\n  To see your new commands:')
    display('    `az {} -h`'.format(group_name))
    display('\n  To discover and run your tests:')
    display('    `azdev test {} --discover`'.format(group_name))
    display('\n  To identify code style issues (there will be some left over from code generation):')
    display('    `azdev style {}`'.format(group_name))
    display('\n  To identify CLI-specific linter violations:')
    display('    `azdev linter {}`'.format(group_name))


def _download_vendored_sdk(required_sdk, path):
    import tempfile
    import zipfile

    path_regex = re.compile(r'.*((\s*.*downloaded\s)|(\s*.*saved\s))(?P<path>.*\.whl)', re.IGNORECASE | re.S)
    temp_path = tempfile.mkdtemp()

    # download and extract the required SDK to the vendored_sdks folder
    downloaded_path = None
    if required_sdk:
        display('Downloading {}...'.format(required_sdk))
        vendored_sdks_path = path
        result = pip_cmd('download {} --no-deps -d {}'.format(required_sdk, temp_path)).result
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
            display('Unable to download')
            raise CLIError('Unable to download: {}'.format(required_sdk))

        # extract the WHL file
        with zipfile.ZipFile(str(downloaded_path), 'r') as z:
            z.extractall(temp_path)

        _copy_vendored_sdk(temp_path, vendored_sdks_path)


def _copy_vendored_sdk(src_path, dest_path):
    import shutil

    try:
        client_location = find_files(src_path, 'version.py')[0]
    except IndexError:
        raise CLIError('Unable to find client files.')

    # copy the client files and folders to the root of vendored_sdks for easier access
    client_dir = os.path.dirname(client_location)
    shutil.rmtree(dest_path)
    shutil.copytree(client_dir, dest_path)


def _add_to_codeowners(repo_path, prefix, name, github_alias):
    # add the user Github alias to the CODEOWNERS file for new packages
    if not github_alias:
        display('\nWhat is the Github alias of the person responsible for maintaining this package?')
        while not github_alias:
            github_alias = prompt('Alias: ')

    # accept a raw alias or @alias
    github_alias = '@{}'.format(github_alias) if not github_alias.startswith('@') else github_alias
    try:
        codeowners = find_files(repo_path, 'CODEOWNERS')[0]
    except IndexError:
        raise CLIError('unexpected error: unable to find CODEOWNERS file.')

    if prefix == EXTENSION_PREFIX:
        new_line = '/src/{}{}/ {}'.format(prefix, name, github_alias)
    else:
        # ensure Linux-style separators when run on Windows
        new_line = '/{} {}'.format(os.path.join('', _MODULE_ROOT_PATH, name, ''), github_alias).replace('\\', '/')

    with open(codeowners, 'a') as f:
        f.write(new_line)
        f.write('\n')


def _add_to_doc_map(repo_path, name):
    try:
        doc_source_file = find_files(repo_path, 'doc_source_map.json')[0]
    except IndexError:
        raise CLIError('unexpected error: unable to find doc_source_map.json file.')
    doc_source = None
    with open(doc_source_file, 'r') as f:
        doc_source = json.loads(f.read())

    # ensure Linux-style separators when run on Windows
    doc_source[name] = str(os.path.join(_MODULE_ROOT_PATH, name, '_help.py')).replace('\\', '/')
    with open(doc_source_file, 'w') as f:
        f.write(json.dumps(doc_source, indent=4))


# pylint: disable=too-many-locals, too-many-statements, too-many-branches
def _create_package(prefix, repo_path, is_ext, name='test', display_name=None, display_name_plural=None,
                    required_sdk=None, client_name=None, operation_name=None, sdk_property=None,
                    not_preview=False, local_sdk=None):
    from jinja2 import Environment, PackageLoader

    if local_sdk and required_sdk:
        raise CLIError('usage error: --local-sdk PATH | --required-sdk NAME==VER')

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
            raise CLIError('aborted by user')

    ext_folder = '{}{}'.format(prefix, name) if is_ext else None

    # create folder tree
    if is_ext:
        _ensure_dir(os.path.join(new_package_path, ext_folder, 'tests', 'latest'))
        _ensure_dir(os.path.join(new_package_path, ext_folder, 'vendored_sdks'))
    else:
        _ensure_dir(os.path.join(new_package_path, 'tests', 'latest'))
    env = Environment(loader=PackageLoader('azdev', 'mod_templates'))

    # determine dependencies
    dependencies = []
    if is_ext:
        dependencies.append("'azure-cli-core'")
        if required_sdk:
            _download_vendored_sdk(
                required_sdk,
                path=os.path.join(new_package_path, ext_folder, 'vendored_sdks')
            )
        elif local_sdk:
            _copy_vendored_sdk(local_sdk, os.path.join(new_package_path, ext_folder, 'vendored_sdks'))
        sdk_path = None
        if any([local_sdk, required_sdk]):
            sdk_path = '{}{}.vendored_sdks'.format(prefix, package_name)
        kwargs.update({
            'sdk_path': sdk_path,
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
    if is_ext:
        root_files = [
            'HISTORY.rst',
            'README.rst',
            'setup.cfg',
            'setup.py'
        ]
        _generate_files(env, kwargs, root_files, dest_path)

    dest_path = dest_path if not is_ext else os.path.join(dest_path, ext_folder)
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

    if is_ext:
        result = pip_cmd('install -e {}'.format(new_package_path), "Installing `{}{}`...".format(prefix, name))
        if result.error:
            raise result.error  # pylint: disable=raising-bad-type


def _get_swagger_readme_file_path(ext_name, swagger_repo, branch):
    swagger_readme_file_path = None
    if swagger_repo == const.GITHUB_SWAGGER_REPO_URL or \
            (swagger_repo.startswith('https://') and swagger_repo.endswith(const.SWAGGER_REPO_NAME)):
        swagger_readme_file_path = '{}/blob/{}/specification/{}/resource-manager'.format(
            swagger_repo, branch, ext_name)
        # validate URL
        try:
            request.urlopen(swagger_readme_file_path)
        except error.HTTPError as ex:
            raise CLIError(
                'HTTPError: {}\nNo swagger readme file found in this URL: {}'.format(ex.code, swagger_readme_file_path))
    else:
        swagger_readme_file_path = os.path.join(swagger_repo, 'specification', ext_name, 'resource-manager')
        if not os.path.isdir(swagger_readme_file_path):
            raise CLIError("The path {} does not exist.".format(swagger_readme_file_path))
    return swagger_readme_file_path


# pylint: disable=too-many-statements
def _generate_extension(ext_name, repo_path, swagger_readme_file_path, use):
    heading('Start generating extension {}.'.format(ext_name))
    # check if npm is installed
    try:
        shell_cmd('npm --version', stdout=subprocess.DEVNULL, raise_ex=False)
    except CLIError as ex:
        raise CLIError('{}\nPlease install npm.'.format(ex))
    display('Installing autorest...\n')
    if const.IS_WINDOWS:
        try:
            shell_cmd('npm install -g autorest', raise_ex=False)
        except CLIError as ex:
            raise CLIError("Failed to install autorest.\n{}".format(ex))
    else:
        try:
            shell_cmd('npm install -g autorest', stderr=subprocess.DEVNULL, raise_ex=False)
        except CLIError as ex:
            path = os.environ['PATH']
            # check if npm is installed through nvm
            if os.environ.get('NVM_DIR'):
                raise ex
            # check if user using specific node version and manually add it to the os env PATH
            node_version = shell_cmd('node --version', capture_output=True).result
            if 'node/' + node_version + '/bin' in path:
                raise ex
            # create a new directory for npm global installations, to avoid using sudo in installing autorest
            npm_path = os.path.join(os.environ['HOME'], '.npm-packages')
            if not os.path.isdir(npm_path):
                os.mkdir(npm_path)
            npm_prefix = shell_cmd('npm prefix -g', capture_output=True).result
            shell_cmd('npm config set prefix ' + npm_path)
            os.environ['PATH'] = path + ':' + os.path.join(npm_path, 'bin')
            os.environ['MANPATH'] = os.path.join(npm_path, 'share', 'man')
            shell_cmd('npm install -g autorest')
            shell_cmd('npm config set prefix ' + npm_prefix)
    # update autorest core
    shell_cmd('autorest --latest')
    if not use:
        cmd = const.AUTO_REST_CMD + '{} {}'.format(repo_path, swagger_readme_file_path)
    else:
        cmd = const.AUTO_REST_CMD + '{} {} --use={}'.format(repo_path, swagger_readme_file_path, use)
    shell_cmd(cmd, message=True)


def _add_extension(ext_name, repo_path):
    new_package_path = os.path.join(repo_path, 'src', ext_name)
    result = pip_cmd('install -e {}'.format(new_package_path), "Adding extension `{}`...".format(new_package_path))
    if result.error:
        raise result.error
