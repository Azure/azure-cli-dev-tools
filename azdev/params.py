# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

# pylint: disable=line-too-long
import argparse

from knack.arguments import ArgumentsContext, CLIArgumentType

from azdev.completer import get_test_completion
from azdev.operations.linter import linter_severity_choices
from azdev.operations.command_change import diff_export_format_choices


class Flag:
    """ Place holder to be used for optionals that take 0 or more arguments """


# pylint: disable=too-many-statements
def load_arguments(self, _):

    modules_type = CLIArgumentType(nargs='*',
                                   help="Space-separated list of modules or extensions (dev mode) to check. "
                                        "Use 'CLI' to check built-in modules or 'EXT' to check extensions. "
                                        "Omit to check all. ")

    with ArgumentsContext(self, '') as c:
        c.argument('private', action='store_true', help='Target the private repo.')
        c.argument('yes', options_list=['--yes', '-y'], action='store_true', help='Answer "yes" to all prompts.')
        c.argument('use_ext_index', action='store_true', help='Run command on extensions registered in the azure-cli-extensions index.json.')
        c.argument('git_source', options_list='--src', arg_group='Git', help='Name of the Git source branch to check (i.e. master or upstream/master).')
        c.argument('git_target', options_list='--tgt', arg_group='Git', help='Name of the Git target branch to check (i.e. dev or upstream/dev)')
        c.argument('git_repo', options_list='--repo', arg_group='Git', help='Path to the Git repo to check.')

    with ArgumentsContext(self, 'setup') as c:
        c.argument('cli_path', options_list=['--cli', '-c'], nargs='?', const=Flag, help="Path to an existing Azure CLI repo. Omit value to search for the repo or use special value 'EDGE' to install the latest developer edge build.")
        c.argument('ext_repo_path', options_list=['--repo', '-r'], nargs='+', help='Space-separated list of paths to existing Azure CLI extensions repos.')
        c.argument('ext', options_list=['--ext', '-e'], nargs='+', help="Space-separated list of extensions to install initially. Use '*' to install all extensions.")
        c.argument('deps', options_list=['--deps-from', '-d'], choices=['requirements.txt', 'setup.py'], default='requirements.txt', help="Choose the file to resolve dependencies.")

    with ArgumentsContext(self, 'test') as c:
        c.argument('discover', options_list='--discover', action='store_true', help='Build an index of test names so that you don\'t need to specify fully qualified test paths.')
        c.argument('xml_path', options_list='--xml-path', help='Path and filename at which to store the results in XML format. If omitted, the file will be saved as `test_results.xml` in your `.azdev` directory.')
        c.argument('in_series', options_list='--series', action='store_true', help='Disable test parallelization.')
        c.argument('run_live', options_list='--live', action='store_true', help='Run all tests live.')

        c.positional('tests', nargs='*',
                     help="Space-separated list of tests to run. Can specify module or extension names, test filenames, class name or individual method names. "
                          "Omit to check all or use 'CLI' or 'EXT' to check only CLI modules or extensions respectively.",
                     completer=get_test_completion)
        c.argument('profile', options_list='--profile', choices=['latest', '2017-03-09-profile', '2018-03-01-hybrid', '2019-03-01-hybrid', '2020-09-01-hybrid'], help='Run automation against a specific profile. If omit, the tests will run against current profile.')
        c.argument('pytest_args', nargs=argparse.REMAINDER, options_list=['--pytest-args', '-a'], help='Denotes the remaining args will be passed to pytest.')
        c.argument('last_failed', options_list='--lf', action='store_true', help='Re-run the last tests that failed.')
        c.argument('no_exit_first', options_list='--no-exitfirst', action='store_true', help='Do not exit on first error or failed test')
        c.argument('mark', help='Select tests with this mark. You can add @pytest.mark.custom_mark to a test')

        # CI parameters
        c.argument('cli_ci',
                   action='store_true',
                   arg_group='Continuous Integration',
                   help='Apply incremental test strategy to Azure CLI on Azure DevOps')

    with ArgumentsContext(self, 'coverage') as c:
        c.argument('prefix', type=str, help='Filter analysis by command prefix.')
        c.argument('report', action='store_true', help='Display results as a report.')
        c.argument('untested_params', nargs='+', help='Space-separated list of param dest values to search for (OR logic)')

    with ArgumentsContext(self, 'style') as c:
        c.positional('modules', modules_type)
        c.argument('pylint', action='store_true', help='Run pylint.')
        c.argument('pep8', action='store_true', help='Run flake8 to check PEP8.')

    with ArgumentsContext(self, 'cli check-versions') as c:
        c.argument('update', action='store_true', help='If provided, the command will update the versions in azure-cli\'s setup.py file.')
        c.argument('pin', action='store_true', help='If provided and used with --update, will pin the module versions in azure-cli\'s setup.py file.')

    with ArgumentsContext(self, 'cli update-setup') as c:
        c.argument('pin', action='store_true', help='Pin the module versions in azure-cli\'s setup.py file.')

    # region linter
    with ArgumentsContext(self, 'linter') as c:
        c.positional('modules', modules_type)
        c.argument('rules', options_list=['--rules', '-r'], nargs='+', help='Space-separated list of rules to run. Omit to run all rules.')
        c.argument('rule_types', options_list=['--rule-types', '-t'], nargs='+', choices=['params', 'commands', 'command_groups', 'help_entries', 'command_test_coverage'], help='Space-separated list of rule types to run. Omit to run all.')
        c.argument('ci_exclusions', action='store_true', help='Force application of CI exclusions list when run locally.')
        c.argument('include_whl_extensions',
                   action='store_true',
                   help="Allow running linter on extensions installed by `az extension add`.")
        c.argument('save_global_exclusion',
                   action='store_true',
                   options_list=['--save', '-s'],
                   help="Allow saving global exclusion. It would take effect when modules is CLI or EXT.",
                   deprecate_info=c.deprecate(hide=True))
        c.argument('min_severity', choices=linter_severity_choices(),
                   help='The minimum severity level to run the linter on. '
                        'For example, specifying "medium" runs linter rules that have "high" or "medium" severity. '
                        'However, specifying "low" runs the linter on every rule, regardless of severity. '
                        'Defaults to "high".')
    # endregion

    # region scan & mask
    for scope in ['scan', 'mask']:
        with ArgumentsContext(self, scope) as c:
            c.argument('file_path', options_list=['--file-path', '-f'],
                       help='Path of the file you want to scan secrets for')
            c.argument('directory_path', options_list=['--directory-path', '-d'],
                       help='Path of the folder you want to scan secrets for')
            c.argument('recursive', options_list=['--recursive', '-r'],
                       help='Scan the directory recursively')
            c.argument('include_pattern', options_list=['--include-pattern', '--include'], nargs='*',
                       help="Space separated patterns used for files you want to include within the directory. "
                            "The supported patterns are '*', '?', '[seq]', and '[!seq]'. "
                            "For more information, please refer to https://docs.python.org/3/library/fnmatch.html")
            c.argument('exclude_pattern', options_list=['--exclude-pattern', '--exclude'], nargs='*',
                       help="Space separated patterns used for files you want to exclude within the directory. "
                            "The supported patterns are '*', '?', '[seq]', and '[!seq]'. "
                            "For more information, please refer to https://docs.python.org/3/library/fnmatch.html")
            c.argument('data', help='Raw string you want to scan secrets for')
            c.argument('save_scan_result', options_list=['--save-scan-result', '--save'], action='store_true',
                       help='Whether to save scan result to file or not')
            c.argument('scan_result_path', options_list=['--scan-result-path', '--result'],
                       help='Path for the file you want to save the result in. '
                            'If specified, --save-scan-result will be True anyway. '
                            'If not speficied but set --save-scan-result to True, '
                            'the file will be saved as `scan_result_YYYYmmddHHMMSS.json` in your `.azdev` directory ')
            c.argument('confidence_level', choices=['HIGH', 'MEDIUM', 'LOW'], default='HIGH',
                       help='Which confidence level can you accept for built-in scanning patterns. If you choose HIGH, '
                            'we will only scan with high confidence level patterns. If you choose MEDIUM, '
                            'we will use patterns of medium confidence level or above, which is medium and high level.')
            c.argument('custom_pattern',
                       help='Additional patterns you want to apply or built-in patterns you want to exclude '
                            'for scanning. Can be json string or path to the json file.')
            c.argument('continue_on_failure', action='store_true',
                       help='If not, the operation will terminate quickly on encountering file operation errors. '
                            'If true, the operation will warning the error for specific file and proceed with other files. '
                            'If not set the default value is false.')

    with ArgumentsContext(self, 'mask') as c:
        c.argument('yes', options_list=['--yes', '-y'], action='store_true', help='Answer "yes" to all prompts.')
        c.argument('redaction_type', options_list=['--redaction-type', '--type'],
                   choices=['FIXED_VALUE', 'FIXED_LENGTH', 'SECRET_NAME', 'CUSTOM'])
        c.argument('saved_scan_result_path', options_list=['--saved-scan-result-path', '--saved-result'],
                   help='Path of the file you saved the scan result in')
    # endregion

    # region statistics
    with ArgumentsContext(self, 'statistics') as c:
        c.argument('include_whl_extensions',
                   action='store_true',
                   help="Allow running linter on extensions installed by `az extension add`.")
        c.argument('statistics_only', action='store_true', help='Show statistics only, without detailed commands.')

    with ArgumentsContext(self, 'statistics list-command-table') as c:
        c.positional('modules', modules_type)

    with ArgumentsContext(self, 'statistics diff-command-tables') as c:
        c.argument('table_path', help='command table json file')
        c.argument('diff_table_path', help='command table json file to diff')
    # endregion

    with ArgumentsContext(self, 'command-change meta-export') as c:
        c.positional('modules', modules_type)
        c.argument('with_help', action="store_true", help="State whether to include help message")
        c.argument('with_example', action="store_true", help="State whether to include examples")
        c.argument('meta_output_path', help='command meta json file path to store')
        c.argument('include_whl_extensions', action='store_true',
                   help="Allow running cmd loader on extensions installed by `az extension add --source xxx.whl`.")

    with ArgumentsContext(self, 'command-change meta-diff') as c:
        c.argument('base_meta_file', required=True, help='command meta json file')
        c.argument('diff_meta_file', required=True, help='command meta json file to diff')
        c.argument('only_break', action="store_true", help='whether include non breaking changes')
        c.argument('output_type', choices=diff_export_format_choices(), default=diff_export_format_choices()[0],
                   help='format to print diff and suggest message')
        c.argument('output_file', help='command meta diff json file path to store')

    with ArgumentsContext(self, 'command-change tree-export') as c:
        c.positional('modules', modules_type)
        c.argument('output_file', help='command tree json file path to store')

    # region cmdcov
    with ArgumentsContext(self, 'cmdcov') as c:
        c.positional('modules', modules_type)
        c.argument('level', choices=['command', 'argument'], help='Run command test coverage in command level or argument level.')
    # endregion

    with ArgumentsContext(self, 'perf') as c:
        c.argument('runs', type=int, help='Number of runs to average performance over.')

    with ArgumentsContext(self, 'perf benchmark') as c:
        c.positional('commands', nargs="*", help="Command prefix to run benchmark. Omit to check all commands with --help.")
        c.argument('top', type=int, help='Show N slowest commands. 0 for all.')

    with ArgumentsContext(self, 'extension') as c:
        c.argument('dist_dir', help='Name of a directory in which to save the resulting WHL files.')

    with ArgumentsContext(self, 'extension publish') as c:
        c.argument('update_index', action='store_true', help='Update the index.json file after publishing is complete.')

    with ArgumentsContext(self, 'extension publish') as c:
        c.argument('storage_account', help='Name of the storage account to publish to. Environment variable: AZDEV_DEFAULTS_STORAGE_ACCOUNT.', arg_group='Storage', configured_default='storage_account')
        c.argument('storage_container', help='Name of the storage container to publish to. Environment variable: AZDEV_DEFAULTS_STORAGE_CONTAINER.', arg_group='Storage', configured_default='storage_container')
        c.argument('storage_account_key', help='Key of the storage account to publish to. ', arg_group='Storage',
                   configured_default='storage_account')

    for scope in ['extension add', 'extension remove', 'extension build', 'extension publish']:
        with ArgumentsContext(self, scope) as c:
            c.positional('extensions', metavar='NAME', nargs='+', help='Space-separated list of extension names.')

    for scope in ['extension repo add', 'extension repo remove']:
        with ArgumentsContext(self, scope) as c:
            c.positional('repos', metavar='PATH', nargs='+', help='Space-separated list of paths to Git repositories.')

    with ArgumentsContext(self, 'extension update-index') as c:
        c.positional('extensions', nargs='+', metavar='URL', help='Space-separated list of URLs to extension WHL files.')

    with ArgumentsContext(self, 'extension cal-next-version') as c:
        c.argument('base_meta_file', required=True, help='command meta json file')
        c.argument('diff_meta_file', required=True, help='command meta json file to diff')
        c.argument('current_version', help='current version from metadata')
        c.argument('is_preview', help='current azext.isPreview from metadata')
        c.argument('is_experimental', help='current azext.isExperimental from metadata')
        c.argument('next_version_pre_tag', help='next version is stable or preview, if not provided, use current stable/preview tag')
        c.argument('next_version_segment_tag', help='used to modify actual major/minor/patch/pre, if provided, increment version as provided')

    with ArgumentsContext(self, 'extension show') as c:
        c.argument('mod_name', required=True, help='installed extension module name')

    with ArgumentsContext(self, 'cli create') as c:
        c.positional('mod_name', help='Name of the module to create.')

    with ArgumentsContext(self, 'cli create') as c:
        c.ignore('local_sdk')

    with ArgumentsContext(self, 'extension create') as c:
        c.positional('ext_name', help='Name of the extension to create.')

    for scope in ['extension create', 'cli create']:
        with ArgumentsContext(self, scope) as c:
            c.argument('github_alias', help='Github alias for the individual who will be the code owner for this package.')
            c.argument('not_preview', action='store_true', help='Do not create template commands under a "Preview" status.')
            c.argument('required_sdk', help='Name and version of the underlying Azure SDK that is published on PyPI. (ex: azure-mgmt-contoso==0.1.0).', arg_group='SDK')
            c.argument('local_sdk', help='Path to a locally saved SDK. Use if your SDK is not available on PyPI.', arg_group='SDK')
            c.argument('client_name', help='Name of the Python SDK client object (ex: ContosoManagementClient).', arg_group='SDK')
            c.argument('operation_name', help='Name of the principal Python SDK operation class (ex: ContosoOperations).', arg_group='SDK')
            c.argument('sdk_property', help='The name of the Python variable that describes the main object name in the SDK calls (i.e.: account_name)', arg_group='SDK')
            c.argument('repo_name', help='Name of the repo the extension will exist in.')
            c.argument('display_name', arg_group='Help', help='Description to display in help text.')
            c.argument('display_name_plural', arg_group='Help', help='Description to display in help text when plural.')

    with ArgumentsContext(self, 'cli generate-docs') as c:
        c.argument('all_profiles', action='store_true',
                   help="If specified, generate docs for all CLI profiles. NOTE: this command updates the current CLI profile and will attempt to reset it to its original value. "
                        "Please check the CLI's profile after running this command.")

    for scope in ['cli', 'extension']:
        with ArgumentsContext(self, '{} generate-docs'.format(scope)) as c:

            c.argument('output_dir', help='Directory to place the generated docs in. Defaults to a temporary directory. '
                                          'If the base directory does not exist, it will be created')
            c.argument('output_type', choices=['xml', 'html', 'text', 'man', 'latex'], default="xml",
                       help='Output type of the generated docs.')

    with ArgumentsContext(self, 'generate-breaking-change-report') as c:
        c.positional('modules', modules_type)
        c.argument('target_version', default='NextWindow',
                   help='Only the breaking changes scheduled prior to the specified version will be displayed. '
                        'The value could be `NextWindow`, `None` or a specified version like `3.0.0`')
        c.argument('source', choices=['deprecate_info', 'pre_announce'], default='pre_announce',
                   help='The source of pre-announced breaking changes. `deprecate_info` represents all breaking changes '
                        'marked through `deprecation_info`; `pre_announce` represents the breaking changes announced in '
                        '`breaking_change.py` file.')
        c.argument('group_by_version', action='store_true',
                   help='If specified, breaking changes would be grouped by their target version as well.')
        c.argument('output_format', choices=['structure', 'markdown'], default='structure',
                   help='Output format of the collected breaking changes.')
        c.argument('no_head', action='store_true', help='Skip head when displaying as markdown.')
        c.argument('no_tail', action='store_true', help='Skip tail when displaying as markdown.')
