# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from knack.commands import CommandGroup


def load_command_table(self, _):

    def operation_group(name):
        return 'azdev.operations.{}#{{}}'.format(name)

    with CommandGroup(self, '', operation_group('setup')) as g:
        g.command('setup', 'setup')

    # TODO: enhance with tox support
    with CommandGroup(self, '', operation_group('tests')) as g:
        g.command('test', 'run_tests')

    with CommandGroup(self, '', operation_group('style')) as g:
        g.command('style', 'check_style')

    with CommandGroup(self, '', operation_group('linter')) as g:
        g.command('linter', 'run_linter')

    with CommandGroup(self, 'verify', operation_group('pypi')) as g:
        g.command('history', 'check_history')

    with CommandGroup(self, 'cli', operation_group('pypi')) as g:
        g.command('check-versions', 'verify_versions')
        g.command('update-setup', 'update_setup_py')

    with CommandGroup(self, 'verify', operation_group('help')) as g:
        g.command('document-map', 'check_document_map')

    with CommandGroup(self, 'verify', operation_group('legal')) as g:
        g.command('license', 'check_license_headers')

    with CommandGroup(self, 'perf', operation_group('performance')) as g:
        g.command('load-times', 'check_load_time')

    # with CommandGroup(self, 'sdk', operation_group('python_sdk')) as g:
    #     g.command('draft', 'install_draft_sdk')

    with CommandGroup(self, 'extension', operation_group('extensions')) as g:
        g.command('add', 'add_extension')
        g.command('remove', 'remove_extension')
        g.command('list', 'list_extensions')
        g.command('build', 'build_extensions')
        g.command('publish', 'publish_extensions')
        g.command('update-index', 'update_extension_index')

    with CommandGroup(self, 'extension repo', operation_group('extensions')) as g:
        g.command('add', 'add_extension_repo')
        g.command('remove', 'remove_extension_repo')
        g.command('list', 'list_extension_repos')

    # TODO: implement
    # with CommandGroup(self, operation_group('help')) as g:
    #     g.command('generate', 'generate_help_xml')
    #     g.command('convert', 'convert_help_to_yaml')

    # TODO: implement
    # with CommandGroup(self, 'coverage', command_path) as g:
    #    g.command('command', 'command_coverage')
    #    g.command('code', 'code_coverage')

    # TODO: implement
    # with CommandGroup(self, 'verify', command_path) as g:
    #    g.command('package', 'verify_packages')
    #    g.command('dependencies', 'verify_dependencies')
