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
    cmd, py_cmd, pip_cmd, find_file, IS_WINDOWS,
    ENV_VAR_TEST_MODULES, ENV_VAR_TEST_LIVE,
    COMMAND_MODULE_PREFIX, EXTENSION_PREFIX,
    make_dirs, get_azdev_config_dir,
    get_core_module_paths, get_command_module_paths, get_extension_paths)

logger = get_logger(__name__)


DEFAULT_RESULT_FILE = 'test_results.xml'
DEFAULT_RESULT_PATH = os.path.join(get_azdev_config_dir(), DEFAULT_RESULT_FILE)


def run_tests(cmd, tests, xml_path=None, ci_mode=False, discover=False, in_series=False,
              run_live=False, profile=None, pytest_args=None):

    from .pytest_runner import get_test_runner

    heading('Run Tests')

    profile = _get_profile(profile)
    test_index = _get_test_index(cmd, profile, discover)
    tests = tests or []

    # resolve the path at which to dump the XML results
    xml_path = xml_path or DEFAULT_RESULT_PATH
    if not xml_path.endswith('.xml'):
        xml_path = os.path.join(xml_path, DEFAULT_RESULT_FILE)

    # process environment variables
    if run_live:
        logger.warning('RUNNING TESTS LIVE')
        os.environ[ENV_VAR_TEST_LIVE] = 'True'

    if os.environ.get(ENV_VAR_TEST_MODULES, None):
        # TODO: Can this be removed?
        display('Test modules list parsed from environment variable {}.'.format(ENV_VAR_TEST_MODULES))
        tests = [m.strip() for m in os.environ.get(ENV_VAR_TEST_MODULES).split(',')]

    if ci_mode:
        # CI Mode runs specific modules
        # TODO: linter was included, but now this will be in azdev...
        module_names = [name for name, _ in get_command_module_paths()]
        core_names = [name for name, _ in get_core_module_paths()]
        tests = module_names + core_names

    # lookup test paths from index
    test_paths = []
    for t in tests:   
        try:
            test_path = os.path.normpath(test_index[t])
            test_paths.append(test_path)
        except KeyError:
            logger.warning("'{}' not found. If newly added, re-run with --discover".format(t))
            continue

    # Tests have been collected. Now run them.
    if not test_paths:
        raise CLIError('No tests selected to run.')

    runner = get_test_runner(parallel=not in_series, log_path=xml_path)
    exit_code = runner(test_paths=test_paths, pytest_args=pytest_args)
    _summarize_test_results(xml_path)

    sys.exit(0 if not exit_code else 1)


def _extract_module_name(path):
    mod_name_regex = re.compile(r'azure-cli-([^/\\]+)[/\\]azure[/\\]cli')
    ext_name_regex = re.compile(r'.*(azext_[^/\\]+).*')

    try:
        return re.search(mod_name_regex, path).group(1)
    except AttributeError:
        return  re.search(ext_name_regex, path).group(1)


def _get_profile(profile):
    import colorama
    colorama.init(autoreset=True)
    try:
        fore_red = colorama.Fore.RED if not IS_WINDOWS else ''
        fore_reset = colorama.Fore.RESET if not IS_WINDOWS else ''
        current_profile = cmd('az cloud show --query profile -otsv', show_stderr=False).result
        if not profile or current_profile == profile:
            profile = current_profile
            display('The tests are set to run against current profile {}.'
                    .format(fore_red + current_profile + fore_reset))
        elif current_profile != profile:
            display('The tests are set to run against profile {} but the current az cloud profile is {}.'
                    .format(fore_red + profile + fore_reset, fore_red + current_profile + fore_reset))
            result = cmd('az cloud update --profile {}'.format(profile), 'SWITCHING TO PROFILE {}.'.format(fore_red + profile + fore_reset))
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
        test_files = {x[:-len('.py')]: {} for x in contents if x.startswith('test_') and x.endswith('.py')}
        total_files = len(test_files)
    except Exception:
        # skip modules that don't have tests
        logger.info('  No test files found.')
        return None

    for file_name in test_files:
        mod_data['files'][file_name] = {}
        test_file_path = mod_data['base_path'] + '.' + file_name
        try:
            module = import_module(test_file_path)
        except ImportError as ex:
            logger.info('    {}'.format(ex))
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


def _discover_tests(profile):
    """ Builds an index of tests so that the user can simply supply the name they wish to test instead of the
        full path. 
    """
    profile_split = profile.split('-')
    profile_namespace = '_'.join([profile_split[-1]] + profile_split[:-1])

    core_modules = get_core_module_paths()
    command_modules = get_command_module_paths(include_prefix=False)
    extensions = get_extension_paths()

    heading('Discovering Tests')

    module_data = {}

    logger.info('\nCore Modules: %s', ', '.join([name for name, _ in core_modules]))
    for mod_name, mod_path in core_modules:
        filepath = mod_path
        for comp in os.path.basename(mod_path).split('-'):
            filepath = os.path.join(filepath, comp)
        mod_data = {
            'filepath': os.path.join(filepath, 'tests'),
            'base_path': 'azure.cli.{}.tests'.format(mod_name),
            'files': {}
        }
        module_data[mod_name] = _discover_module_tests(mod_name, mod_data)

    logger.info('\nCommand Modules: %s', ', '.join([name for name, _ in command_modules]))
    for mod_name, mod_path in command_modules:
        mod_data = {
            'filepath': os.path.join(mod_path, 'azure', 'cli', 'command_modules', mod_name, 'tests', profile_namespace),
            'base_path': 'azure.cli.command_modules.{}.tests.{}'.format(mod_name, profile_namespace),
            'files': {}
        }
        module_data[mod_name] = _discover_module_tests(mod_name, mod_data)

    logger.info('\nExtensions: %s', ', '.join([name for name, _ in extensions]))
    for mod_name, mod_path in extensions:
        glob_pattern = os.path.normcase(os.path.join('{}*'.format(EXTENSION_PREFIX)))
        filepath = glob.glob(os.path.join(mod_path, glob_pattern))[0]
        import_name = os.path.basename(filepath)
        mod_data = {
            'filepath': os.path.join(filepath, 'tests', profile_namespace),
            'base_path': '{}.tests.{}'.format(import_name, profile_namespace),
            'files': {}
        }
        module_data[import_name] = _discover_module_tests(import_name, mod_data)

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
                logger.warning("'{key}' exists in both '{mod1}' and '{mod2}'. Resolve using `{mod1}.{key}` or `{mod2}.{key}`".format(key=key, mod1=mod1, mod2=mod2))
                test_index['{}.{}'.format(mod1, key)] = path
                test_index['{}.{}'.format(mod2, key)] = test_index[key]
            else:
                logger.error("'{}' exists twice in the '{}' module. Please rename one or both and re-run --discover.".format(key, mod1))
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

    # remove the conflicted keys since they would arbitrarily point to a random implementation
    for key in conflicted_keys:
        del test_index[key]

    return test_index


def _get_test_index(cmd, profile, discover):
    test_index_dir = os.path.join(cmd.cli_ctx.config.config_dir, 'test_index')
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
    display('Time: {time} sec\tTests: {tests}\tSkipped: {skips}\tFailures: {failures}\tErrors: {errors}'.format(**summary))

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
