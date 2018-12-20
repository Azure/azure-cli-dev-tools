# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from docutils import core, io
import os
import sys
try:
    import xmlrpclib
except ImportError:
    import xmlrpc.client as xmlrpclib  # pylint: disable=import-error


from azdev.utilities import (
    display, heading, subheading, cmd, py_cmd, get_cli_repo_path, get_path_table,
    pip_cmd, call)

from knack.log import get_logger
from knack.util import CLIError

logger = get_logger(__name__)


HISTORY_NAME = 'HISTORY.rst'
RELEASE_HISTORY_TITLE = 'Release History'
SETUP_PY_NAME = 'setup.py'

# region verify History Headings
def check_history(modules=None):
    # TODO: Does not work with extensions
    path_table = get_path_table(include_only=modules)
    selected_modules = list(path_table['core'].items()) + list(path_table['mod'].items())

    heading('Verify History')

    module_names = sorted([name for name, _ in selected_modules])
    display('Verifying README and HISTORY files for modules: {}'.format(' '.join(module_names)))

    failed_mods = []
    for name, path in selected_modules:
        errors = _check_readme_render(path)
        if errors:
            failed_mods.append(name)
            subheading('{} errors'.format(name))
            for error in errors:
                logger.error('%s\n', error)
    subheading('Results')
    if failed_mods:
        display('The following modules have invalid README/HISTORYs:')
        logger.error('\n'.join(failed_mods))
        logger.warning('See above for the full warning/errors')
        logger.warning('note: Line numbers in the errors map to the long_description of your setup.py.')
        sys.exit(1)
    display('OK')


def _check_history_headings(mod_path):
    history_path = os.path.join(mod_path, HISTORY_NAME)

    source_path = None
    destination_path = None
    errors = []
    with open(history_path, 'r') as f:
        input_string = f.read()
        _, pub = core.publish_programmatically(
            source_class=io.StringInput, source=input_string,
            source_path=source_path,
            destination_class=io.NullOutput, destination=None,
            destination_path=destination_path,
            reader=None, reader_name='standalone',
            parser=None, parser_name='restructuredtext',
            writer=None, writer_name='null',
            settings=None, settings_spec=None, settings_overrides={},
            config_section=None, enable_exit_status=None)

        # Check first heading is Release History
        if pub.writer.document.children[0].rawsource != RELEASE_HISTORY_TITLE:
            errors.append("Expected '{}' as first heading in HISTORY.rst".format(RELEASE_HISTORY_TITLE))

        all_versions = [t['names'][0] for t in pub.writer.document.children if t['names']]
        # Check that no headings contain 'unreleased'. We don't require it any more
        if any('unreleased' in v.lower() for v in all_versions):
            errors.append("We no longer require 'unreleased' in headings. Use the appropriate version number instead.")

        # Check that the current package version has a history entry
        if not all_versions:
            errors.append("Unable to get versions from {}. Check formatting. e.g. there should be a new line after the 'Release History' heading.".format(history_path))

        first_version_history = all_versions[0]
        actual_version = cmd('python setup.py --version', cwd=mod_path)
        actual_version = actual_version.result.strip()
        if first_version_history != actual_version:
            errors.append("The topmost version in {} does not match version {} defined in setup.py.".format(history_path, actual_version))
    return errors


def _check_readme_render(mod_path):
    errors = []
    result = cmd('python setup.py check -r -s', cwd=mod_path)
    if result.exit_code:
        # this outputs some warnings we don't care about
        error_lines = []
        target_line = 'The following syntax errors were detected'
        suppress = True
        for line in result.error.output.splitlines():
            if not suppress and line:
                error_lines.append(line)
            if target_line in line:
                suppress = False
        errors.append(os.linesep.join(error_lines))
    errors += _check_history_headings(mod_path)
    return errors
# endregion


# region verify PyPI versions
# def check_versions(modules=None, base_repo=None, base_tag=None):
#     path_table = get_path_table(include_only=modules)
#     selected_modules = list(path_table['core'].items()) + list(path_table['mod'].items())
#     base_repo = base_repo or get_cli_repo_path()

#     heading('Verify PyPI Verions')

#     module_names = sorted([name for name, _ in selected_modules])
#     display('Verifying PyPI versions for modules: {}'.format(' '.join(module_names)))

#     failed_mods = []
#     for name, path in selected_modules:
#         errors = _check_package_version(name, path, base_repo=base_repo, base_tag=base_tag)
#         if errors:
#             failed_mods.append(name)
#             subheading('{} errors'.format(name))
#             for error in errors:
#                 logger.error('%s\n', error)
#     subheading('Results')
#     if failed_mods:
#         display('The following modules have invalid versions:')
#         logger.error('\n'.join(failed_mods))
#         logger.warning('See above for the full warning/errors')
#         sys.exit(1)
#     display('OK')


# def check_versions_on_pypi(package_name, versions=None):
#     """ Query PyPI for package versions.

#     :param package_name: Name of the package on PyPI.
#     :module_version: The version(s) to query. Omit to return all versions.
#     :return [str] sorted list of version strings that match.
#     """
#     if isinstance(versions, str):
#         versions = [versions]

#     client = xmlrpclib.ServerProxy('https://pypi.python.org/pypi')
#     available_versions = sorted(client.package_releases(package_name, True))
#     if not versions:
#         return available_versions
#     return [v for v in available_versions if v in versions]


# def _get_mod_version(mod_path):
#     return cmd('python setup.py --version', cwd=mod_path).result


# def _check_package_version(mod_name, mod_path, base_repo=None, base_tag=None):
#     mod_version = _get_mod_version(mod_path)
#     package_name = 'azure-cli-{}'.format(mod_name)
#     errors = []
#     errors.append(_is_unreleased_version(package_name, mod_version))
#     #errors.append(_is_latest_version(package_name, mod_version))
#     errors.append(_contains_no_plus_dev(mod_version))
#     errors.append(_changes_require_version_bump(package_name, mod_version, mod_path, base_repo=base_repo, base_tag=base_tag))

#     # filter out "None" results
#     errors = [e for e in errors if e]
#     return errors


# def _is_unreleased_version(package_name, mod_version):
#     if check_versions_on_pypi(package_name, mod_version):
#         return '{} {} is already available on PyPI! Update the version.'.format(package_name, mod_version)


# def _is_latest_version(package_name, mod_version):
#     latest = check_versions_on_pypi(package_name)[-1]
#     if mod_version != latest:
#         return '{} {} is not the latest version on PyPI! Use version {}.'.format(package_name, mod_version, latest)


# def _contains_no_plus_dev(mod_version):
#     if '+dev' in mod_version:
#         return "Version contains the invalid '+dev'. Actual version {}".format(mod_version)


# def _changes_require_version_bump(package_name, mod_version, mod_path, base_repo=None, base_tag=None):
#     revision_range = os.environ.get('TRAVIS_COMMIT_RANGE', None)
#     if not revision_range:
#         # TODO: Shoud not depend on CI! Must be able to run locally.
#         # TRAVIS_COMMIT_RANGE looks like <ID>...<ID>
#         # 
#         pass
#     error = None
#     if revision_range:
#         changes = cmd('git diff {} -- {} :(exclude)*/tests/*'.format(revision_range, mod_path)).result
#         if changes:
#             if check_versions_on_pypi(package_name, mod_version):
#                 error = 'There are changes to {} and the current version {} is already available on PyPI! Bump the version.'.format(package_name, mod_version)
#             elif base_repo and _version_in_base_repo(base_repo, mod_path, package_name, mod_version):
#                 error = 'There are changes to {} and the current version {} is already used at tag {}. Bump the version.'.format(package_name, mod_version, base_tag)
#             error += '\nChanges are as follows:'
#             error += changes
#     return error


# def _version_in_base_repo(base_repo, mod_path, package_name, mod_version):
#     cli_path = get_cli_repo_path()
#     base_repo_mod_path = mod_path.replace(cli_path, base_repo)
#     try:
#         if mod_version == _get_mod_version(base_repo_mod_path):
#             logger.error('Version %s of %s is already used in the base repo.', mod_version, package_name)
#             return True
#     except FileNotFoundError:
#         logger.warning('Module %s not in base repo. Skipping...', package_name)
#     except Exception as ex:
#         # warning if unable to get module from base version (e.g. mod didn't exist there)
#         logger.warning('Warning: Unable to get module version from base repo... skipping...')
#         logger.warning(str(ex))
#     return False
# endregion


# region verify PyPI versions
def verify_versions(modules=None):
    import tempfile
    import shutil

    heading('Verify Package Versions')

    original_cwd = os.getcwd()
    path_table = get_path_table(include_only=modules)
    modules = list(path_table['core'].items()) + list(path_table['mod'].items())

    display('MODULES: {}'.format(', '.join([x[0] for x in modules])))

    temp_dir = tempfile.mkdtemp()

    results = {}
    for mod, mod_path in modules:
        # currently, this is not published
        if mod == 'azure-cli-testsdk':
            continue
        results.update(_check_module(temp_dir, mod, mod_path))

    shutil.rmtree(temp_dir)
    os.chdir(original_cwd)

    failed_mods = {k: v for k, v in results.items() if v['status'] != 'OK'}
    subheading('RESULTS')
    if failed_mods:
        logger.error('The following modules need their versions bumped. Scroll up for details: %s', ', '.join(failed_mods.keys()))
        logger.warning('\nNote that before changing versions, you should consider running `git clean` to remove untracked files from your repo. '
                       'Files that were once tracked but removed from the source may still be on your machine, resuling in false positives.')
    else:
        display('OK!')


def _check_module(root_dir, mod, mod_path):
    import re
    import zipfile

    version_pattern = re.compile(r'.*azure_cli[^-]*-(\d*.\d*.\d*).*')

    results = {}
    downloaded_path = None
    downloaded_version = None
    build_path = None
    build_version = None

    build_dir = os.path.join(root_dir, mod, 'local')
    pypi_dir = os.path.join(root_dir, mod, 'public')

    # download the public PyPI package and extract the version
    result = pip_cmd('download {} --no-deps -d {}'.format(mod, root_dir)).result
    for line in result.splitlines():
        if line.endswith('.whl') and line.startswith('Saved'):
            downloaded_path = line.replace('Saved ', '').strip()
            downloaded_version = version_pattern.match(downloaded_path).group(1)
            break

    # build from source and extract the version
    setup_path = os.path.normpath(mod_path.strip())
    os.chdir(setup_path)
    py_cmd('setup.py bdist_wheel -d {}'.format(build_dir))
    if len(os.listdir(build_dir)) != 1:
        raise CLIError('Unexpectedly found multiple build files found in {}.'.format(build_dir))
    build_path = os.path.join(build_dir, os.listdir(build_dir)[0])
    build_version = version_pattern.match(build_path).group(1)

    if build_version != downloaded_version:
        # TODO: Make this more robust? What if local version < public?
        results[mod] = {
            'local_version': build_version,
            'public_version': downloaded_version,
            'status': 'OK'
        }
    else:
        # slight difference in dist-info dirs, so we must extract the azure folders and compare them
        with zipfile.ZipFile(str(downloaded_path), 'r') as z:
            z.extractall(pypi_dir)

        with zipfile.ZipFile(str(build_path), 'r') as z:
            z.extractall(build_dir)

        errors = _compare_folders(os.path.join(pypi_dir), os.path.join(build_dir))
        # clean up empty strings
        errors = [e for e in errors if e]
        if errors:
            subheading('Differences found in {}'.format(mod))
            for error in errors:
                logger.warning(error)
        results[mod] = {
            'local_version': build_version,
            'public_version': downloaded_version,
            'status': 'OK' if not errors else 'ERROR'
        }

        # special case: to make a release, these MUST be bumped
        if mod in ['azure-cli', 'azure-cli-core']:
            if results[mod]['status'] == 'OK':
                logger.warning('%s version must be bumped to support release!', mod)
                results[mod]['status'] = 'ERROR'

    return results


def _diff_files(filename, dir1, dir2):
    import difflib
    file1 = os.path.join(dir1, filename)
    file2 = os.path.join(dir2, filename)
    errors = []
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        errors.append(os.linesep.join(diff for diff in difflib.context_diff(f1.readlines(), f2.readlines())))
    return errors


def _compare_common_files(common_files, dir1, dir2):
    import hashlib
    errors = []
    for filename in common_files:
        errors = errors + _diff_files(filename, dir1, dir2)
    return errors


def _compare_folders(dir1, dir2):
    import filecmp
    dirs_cmp = filecmp.dircmp(dir1, dir2)
    errors = []
    if len(dirs_cmp.left_only) > 0 or len(dirs_cmp.right_only) > 0 or len(dirs_cmp.funny_files) > 0:
        # allow some special cases
        if len(dirs_cmp.left_only) == 1 and '__init__.py' in dirs_cmp.left_only:
            pass
        elif len(dirs_cmp.right_only) == 1 and dirs_cmp.right_only[0].endswith('.whl'):
            pass
        else:
            if dirs_cmp.left_only:
                logger.debug('LO: %s', dirs_cmp.left_only)
            if dirs_cmp.right_only:
                logger.debug('RO: %s', dirs_cmp.right_only)
            if dirs_cmp.funny_files:
                logger.debug('FF: %s', dirs_cmp.funny_files)
            errors.append('Different files in directory structure.')
    errors = errors + _compare_common_files(dirs_cmp.common_files, dir1, dir2)
    for common_dir in dirs_cmp.common_dirs:
        new_dir1 = os.path.join(dir1, common_dir)
        new_dir2 = os.path.join(dir2, common_dir)
        if common_dir.endswith('.dist-info'):
            # special case to check for dependency-only changes
            errors = errors + _compare_dependencies(new_dir1, new_dir2)
        else:
            errors = errors + _compare_folders(new_dir1, new_dir2)
    return errors


def _extract_dependencies(path):
    dependencies = {}
    with open(path, 'r') as f:
        for line in f.readlines():
            if line.startswith('Requires-Dist:'):
                line = line.replace(' ;', '').replace(';', '')
                comps = line.split(' ', 2)
                if len(comps) == 2:
                    dependencies[comps[1]] = '_ANY_'
                elif len(comps) > 2:
                    dependencies[comps[1]] = comps[2]
                else:
                    raise CLIError('Unrecognized format in METADATA: {}'.format(line))
    return dependencies


def _compare_dependencies(dir1, dir2):
    deps1 = _extract_dependencies(os.path.join(dir1, 'METADATA'))
    deps2 = _extract_dependencies(os.path.join(dir2, 'METADATA'))
    errors = []
    mismatch = {}
    matched = []
    for key, val in deps1.items():
        if key in deps2:
            if deps2[key] != val:
                mismatch[key] = '{} != {}'.format(val, deps2[key])
            deps2.pop(key)
            matched.append(key)
    for key in matched:
        deps1.pop(key)
    for key, val in deps2.items():
        if key in deps1:
            if deps1[key] != val:
                mismatch[key] = '{} != {}'.format(val, deps1[key])
            deps1.pop(key)
    if deps1:
        errors.append('New dependencies: {}'.format(deps1))
    if deps2:
        errors.append('Removed dependencies: {}'.format(deps2))
    if mismatch:
        errors.append('Changed dependencies: {}'.format(mismatch))
    return errors
# endregion
