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
    display, heading, subheading, cmd, py_cmd, get_core_module_paths, get_command_module_paths,
    get_cli_repo_path, filter_module_paths
)

from knack.log import get_logger

logger = get_logger(__name__)


HISTORY_NAME = 'HISTORY.rst'
RELEASE_HISTORY_TITLE = 'Release History'
SETUP_PY_NAME = 'setup.py'

# region verify History Headings
def check_history(modules=None):
    all_modules = get_core_module_paths() + get_command_module_paths()
    selected_modules = filter_module_paths(all_modules, modules)

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
def check_versions(modules=None, base_repo=None, base_tag=None):
    all_modules = get_core_module_paths() + get_command_module_paths()
    selected_modules = filter_module_paths(all_modules, modules)
    base_repo = base_repo or get_cli_repo_path()

    heading('Verify PyPI Verions')

    module_names = sorted([name for name, _ in selected_modules])
    display('Verifying PyPI versions for modules: {}'.format(' '.join(module_names)))

    failed_mods = []
    for name, path in selected_modules:
        errors = _check_package_version(name, path, base_repo=base_repo, base_tag=base_tag)
        if errors:
            failed_mods.append(name)
            subheading('{} errors'.format(name))
            for error in errors:
                logger.error('%s\n', error)
    subheading('Results')
    if failed_mods:
        display('The following modules have invalid versions:')
        logger.error('\n'.join(failed_mods))
        logger.warning('See above for the full warning/errors')
        sys.exit(1)
    display('OK')


def check_versions_on_pypi(package_name, versions=None):
    """ Query PyPI for package versions.

    :param package_name: Name of the package on PyPI.
    :module_version: The version(s) to query. Omit to return all versions.
    :return [str] sorted list of version strings that match.
    """
    if isinstance(versions, str):
        versions = [versions]

    client = xmlrpclib.ServerProxy('https://pypi.python.org/pypi')
    available_versions = sorted(client.package_releases(package_name, True))
    if not versions:
        return available_versions
    return [v for v in available_versions if v in versions]


def _get_mod_version(mod_path):
    return cmd('python setup.py --version', cwd=mod_path).result


def _check_package_version(mod_name, mod_path, base_repo=None, base_tag=None):
    mod_version = _get_mod_version(mod_path)
    package_name = 'azure-cli-{}'.format(mod_name)
    errors = []
    errors.append(_is_unreleased_version(package_name, mod_version))
    #errors.append(_is_latest_version(package_name, mod_version))
    errors.append(_contains_no_plus_dev(mod_version))
    errors.append(_changes_require_version_bump(package_name, mod_version, mod_path, base_repo=base_repo, base_tag=base_tag))

    # filter out "None" results
    errors = [e for e in errors if e]
    return errors


def _is_unreleased_version(package_name, mod_version):
    if check_versions_on_pypi(package_name, mod_version):
        return '{} {} is already available on PyPI! Update the version.'.format(package_name, mod_version)


def _is_latest_version(package_name, mod_version):
    latest = check_versions_on_pypi(package_name)[-1]
    if mod_version != latest:
        return '{} {} is not the latest version on PyPI! Use version {}.'.format(package_name, mod_version, latest)


def _contains_no_plus_dev(mod_version):
    if '+dev' in mod_version:
        return "Version contains the invalid '+dev'. Actual version {}".format(mod_version)


def _changes_require_version_bump(package_name, mod_version, mod_path, base_repo=None, base_tag=None):
    revision_range = os.environ.get('TRAVIS_COMMIT_RANGE', None)
    if not revision_range:
        # TODO: Shoud not depend on CI! Must be able to run locally.
        # TRAVIS_COMMIT_RANGE looks like <ID>...<ID>
        # 
        pass
    error = None
    if revision_range:
        changes = cmd('git diff {} -- {} :(exclude)*/tests/*'.format(revision_range, mod_path)).result
        if changes:
            if check_versions_on_pypi(package_name, mod_version):
                error = 'There are changes to {} and the current version {} is already available on PyPI! Bump the version.'.format(package_name, mod_version)
            elif base_repo and _version_in_base_repo(base_repo, mod_path, package_name, mod_version):
                error = 'There are changes to {} and the current version {} is already used at tag {}. Bump the version.'.format(package_name, mod_version, base_tag)
            error += '\nChanges are as follows:'
            error += changes
    return error


def _version_in_base_repo(base_repo, mod_path, package_name, mod_version):
    cli_path = get_cli_repo_path()
    base_repo_mod_path = mod_path.replace(cli_path, base_repo)
    try:
        if mod_version == _get_mod_version(base_repo_mod_path):
            logger.error('Version %s of %s is already used in the base repo.', mod_version, package_name)
            return True
    except FileNotFoundError:
        logger.warning('Module %s not in base repo. Skipping...', package_name)
    except Exception as ex:
        # warning if unable to get module from base version (e.g. mod didn't exist there)
        logger.warning('Warning: Unable to get module version from base repo... skipping...')
        logger.warning(str(ex))
    return False
# endregion