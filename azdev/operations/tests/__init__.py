# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import glob
from importlib import import_module
import json
import os
import re
from subprocess import CalledProcessError
import sys

from knack.log import get_logger
from knack.util import CLIError

from azdev.utilities import (
    display, output, heading, subheading,
    cmd as raw_cmd, py_cmd, pip_cmd, find_file, IS_WINDOWS,
    ENV_VAR_TEST_LIVE,
    COMMAND_MODULE_PREFIX, EXTENSION_PREFIX,
    make_dirs, get_azdev_config_dir,
    get_path_table, require_virtual_env)

logger = get_logger(__name__)


def run_tests(tests, xml_path=None, discover=False, in_series=False,
              run_live=False, profile=None, last_failed=False, pytest_args=None):

    require_virtual_env()

    DEFAULT_RESULT_FILE = 'test_results.xml'
    DEFAULT_RESULT_PATH = os.path.join(get_azdev_config_dir(), DEFAULT_RESULT_FILE)

    from .pytest_runner import get_test_runner

    heading('Run Tests')

    profile = _get_profile(profile)
    path_table = get_path_table()
    test_index = _get_test_index(profile, discover)
    tests = tests or list(path_table['mod'].keys()) + list(path_table['core'].keys())

    if tests:
        display('\nTESTS: {}\n'.format(', '.join(tests)))

    # resolve the path at which to dump the XML results
    xml_path = xml_path or DEFAULT_RESULT_PATH
    if not xml_path.endswith('.xml'):
        xml_path = os.path.join(xml_path, DEFAULT_RESULT_FILE)

    # process environment variables
    if run_live:
        logger.warning('RUNNING TESTS LIVE')
        os.environ[ENV_VAR_TEST_LIVE] = 'True'

    def _find_test(index, name):
        name_comps = name.split('.')
        num_comps = len(name_comps)
        key_error = KeyError()
        for i in range(num_comps):
            check_name = '.'.join(name_comps[(-1 - i):])
            try:
                match = index[check_name]
                if check_name != name:
                    logger.info("Test found using just '%s'. The rest of the name was ignored.\n", check_name)
                return match
            except KeyError as ex:
                key_error = ex
                continue
        raise key_error

    # lookup test paths from index
    test_paths = []
    for t in tests:
        try:
            test_path = os.path.normpath(_find_test(test_index, t))
            test_paths.append(test_path)
        except KeyError:
            logger.warning("'%s' not found. If newly added, re-run with --discover", t)
            continue

    # Tests have been collected. Now run them.
    if not test_paths:
        raise CLIError('No tests selected to run.')

    runner = get_test_runner(parallel=not in_series, log_path=xml_path, last_failed=last_failed)
    exit_code = runner(test_paths=test_paths, pytest_args=pytest_args)
    _summarize_test_results(xml_path)

    sys.exit(0 if not exit_code else 1)


def _extract_module_name(path):
    mod_name_regex = re.compile(r'azure-cli-([^/\\]+)[/\\]azure[/\\]cli')
    ext_name_regex = re.compile(r'.*(azext_[^/\\]+).*')

    try:
        return re.search(mod_name_regex, path).group(1)
    except AttributeError:
        return re.search(ext_name_regex, path).group(1)


def _get_profile(profile):
    import colorama
    colorama.init(autoreset=True)
    try:
        fore_red = colorama.Fore.RED if not IS_WINDOWS else ''
        fore_reset = colorama.Fore.RESET if not IS_WINDOWS else ''
        current_profile = raw_cmd('az cloud show --query profile -otsv', show_stderr=False).result
        if not profile or current_profile == profile:
            profile = current_profile
            display('The tests are set to run against current profile {}.'
                    .format(fore_red + current_profile + fore_reset))
        elif current_profile != profile:
            display('The tests are set to run against profile {} but the current az cloud profile is {}.'
                    .format(fore_red + profile + fore_reset, fore_red + current_profile + fore_reset))
            result = raw_cmd('az cloud update --profile {}'.format(profile),
                             'SWITCHING TO PROFILE {}.'.format(fore_red + profile + fore_reset))
            if result.exit_code != 0:
                raise CLIError(result.error.output)
        return current_profile
    except CalledProcessError:
        raise CLIError('Failed to retrieve current az profile')


def _discover_module_tests(mod_name, mod_data):

    # get the list of test files in each module
    total_tests = 0
    total_files = 0
    logger.info('Mod: %s', mod_name)
    try:
        contents = os.listdir(mod_data['filepath'])
        test_files = {
            x[:-len('.py')]: {} for x in contents if x.startswith('test_') and x.endswith('.py')
        }
        total_files = len(test_files)
    except (OSError, IOError) as ex:
        err_string = str(ex)
        if 'system cannot find the path' in err_string or 'No such file or directory' in err_string:
            # skip modules that don't have tests
            logger.info('  No test files found.')
            return None
        raise

    for file_name in test_files:
        mod_data['files'][file_name] = {}
        test_file_path = mod_data['base_path'] + '.' + file_name
        try:
            module = import_module(test_file_path)
        except ImportError as ex:
            logger.info('    %s', ex)
            continue
        module_dict = module.__dict__
        possible_test_classes = {x: y for x, y in module_dict.items() if not x.startswith('_')}
        for class_name, class_def in possible_test_classes.items():
            try:
                class_dict = class_def.__dict__
            except AttributeError:
                # skip non-class symbols in files like constants, imported methods, etc.
                continue
            if class_dict.get('__module__') == test_file_path:
                tests = [x for x in class_def.__dict__ if x.startswith('test_')]
                if tests:
                    mod_data['files'][file_name][class_name] = tests
                total_tests += len(tests)
    logger.info('  %s tests found in %s files.', total_tests, total_files)
    return mod_data


# pylint: disable=too-many-statements, too-many-locals
def _discover_tests(profile):
    """ Builds an index of tests so that the user can simply supply the name they wish to test instead of the
        full path.
    """
    profile_split = profile.split('-')
    profile_namespace = '_'.join([profile_split[-1]] + profile_split[:-1])

    heading('Discovering Tests')

    path_table = get_path_table()
    core_modules = path_table['core'].items()
    command_modules = path_table['mod'].items()
    extensions = path_table['ext'].items()

    module_data = {}

    logger.info('\nCore Modules: %s', ', '.join([name for name, _ in core_modules]))
    for mod_name, mod_path in core_modules:
        filepath = mod_path
        for comp in mod_name.split('-'):
            filepath = os.path.join(filepath, comp)
        mod_data = {
            'alt_name': 'main' if mod_name == 'azure-cli' else mod_name.replace(COMMAND_MODULE_PREFIX, ''),
            'filepath': os.path.join(filepath, 'tests'),
            'base_path': '{}.tests'.format(mod_name).replace('-', '.'),
            'files': {}
        }
        tests = _discover_module_tests(mod_name, mod_data)
        if tests:
            module_data[mod_name] = tests

    logger.info('\nCommand Modules: %s', ', '.join([name for name, _ in command_modules]))
    for mod_name, mod_path in command_modules:
        short_name = mod_name.replace(COMMAND_MODULE_PREFIX, '')
        mod_data = {
            'alt_name': short_name,
            'filepath': os.path.join(
                mod_path, 'azure', 'cli', 'command_modules', short_name, 'tests', profile_namespace),
            'base_path': 'azure.cli.command_modules.{}.tests.{}'.format(short_name, profile_namespace),
            'files': {}
        }
        tests = _discover_module_tests(mod_name, mod_data)
        if tests:
            module_data[mod_name] = tests

    logger.info('\nExtensions: %s', ', '.join([name for name, _ in extensions]))
    for mod_name, mod_path in extensions:
        glob_pattern = os.path.normcase(os.path.join('{}*'.format(EXTENSION_PREFIX)))
        try:
            filepath = glob.glob(os.path.join(mod_path, glob_pattern))[0]
        except IndexError:
            logger.debug("No extension found at: %s", os.path.join(mod_path, glob_pattern))
        import_name = os.path.basename(filepath)
        mod_data = {
            'alt_name': os.path.split(filepath)[1],
            'filepath': os.path.join(filepath, 'tests', profile_namespace),
            'base_path': '{}.tests.{}'.format(import_name, profile_namespace),
            'files': {}
        }
        tests = _discover_module_tests(import_name, mod_data)
        if tests:
            module_data[mod_name] = tests

    test_index = {}
    conflicted_keys = []

    def add_to_index(key, path):

        key = key or mod_name
        if key in test_index:
            if key not in conflicted_keys:
                conflicted_keys.append(key)
            mod1 = _extract_module_name(path)
            mod2 = _extract_module_name(test_index[key])
            if mod1 != mod2:
                # resolve conflicted keys by prefixing with the module name and a dot (.)
                logger.warning("'%s' exists in both '%s' and '%s'. Resolve using `%s.%s` or `%s.%s`",
                               key, mod1, mod2, mod1, key, mod2, key)
                test_index['{}.{}'.format(mod1, key)] = path
                test_index['{}.{}'.format(mod2, key)] = test_index[key]
            else:
                logger.error("'%s' exists twice in the '%s' module. "
                             "Please rename one or both and re-run --discover.", key, mod1)
        else:
            test_index[key] = path

    # build the index
    for mod_name, mod_data in module_data.items():
        # don't add empty mods to the index
        if not mod_data:
            continue

        mod_path = mod_data['filepath']
        for file_name, file_data in mod_data['files'].items():
            file_path = os.path.join(mod_path, file_name) + '.py'
            for class_name, test_list in file_data.items():
                for test_name in test_list:
                    test_path = '{}::{}::{}'.format(file_path, class_name, test_name)
                    add_to_index(test_name, test_path)
                class_path = '{}::{}'.format(file_path, class_name)
                add_to_index(class_name, class_path)
            add_to_index(file_name, file_path)
        add_to_index(mod_name, mod_path)
        add_to_index(mod_data['alt_name'], mod_path)

    # remove the conflicted keys since they would arbitrarily point to a random implementation
    for key in conflicted_keys:
        del test_index[key]

    return test_index


def _get_test_index(profile, discover):
    config_dir = get_azdev_config_dir()
    test_index_dir = os.path.join(config_dir, 'test_index')
    make_dirs(test_index_dir)
    test_index_path = os.path.join(test_index_dir, '{}.json'.format(profile))
    test_index = {}
    if discover:
        test_index = _discover_tests(profile)
        with open(test_index_path, 'w') as f:
            f.write(json.dumps(test_index))
        display('\ntest index updated: {}'.format(test_index_path))
    elif os.path.isfile(test_index_path):
        with open(test_index_path, 'r') as f:
            test_index = json.loads(''.join(f.readlines()))
        display('\ntest index found: {}'.format(test_index_path))
    else:
        test_index = _discover_tests(profile)
        with open(test_index_path, 'w') as f:
            f.write(json.dumps(test_index))
        display('\ntest index created: {}'.format(test_index_path))
    return test_index


def _summarize_test_results(xml_path):
    import xml.etree.ElementTree as ElementTree

    subheading('Results')

    root = ElementTree.parse(xml_path).getroot()
    summary = {
        'time': root.get('time'),
        'tests': root.get('tests'),
        'skips': root.get('skips'),
        'failures': root.get('failures'),
        'errors': root.get('errors')
    }
    display('Time: {time} sec\tTests: {tests}\tSkipped: {skips}\tFailures: {failures}\tErrors: {errors}'.format(
        **summary))

    failed = []
    for item in root.findall('testcase'):
        if item.findall('failure'):
            file_and_class = '.'.join(item.get('classname').split('.')[-2:])
            failed.append('{}.{}'.format(file_and_class, item.get('name')))

    if failed:
        subheading('FAILURES')
        for name in failed:
            display(name)
    display('')
