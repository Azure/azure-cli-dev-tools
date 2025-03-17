.. :changelog:

Release History
===============
0.1.96
++++++
* `azdev generate-breaking-change-report`: Add `--no-head` and `--no-tail` to support trim header and tail in markdown report.

0.1.95
++++++
* `azdev generate-breaking-change-report`: Extracts upcoming breaking changes in extensions, regardless of the target version set
* `azdev generate-breaking-change-report`: Fix collecting announcement starting with `az`


0.1.94
++++++
* `azdev command-change meta-export`: Enable meta exporting for extension installed using `.whl` package by `include_whl_extensions`

0.1.93
++++++
* `azdev linter`: Fix `None` path for added files in `git diff` for `missing_command_example` rule

0.1.92
++++++
* `azdev linter`: Add `missing_command_example` rule
* `azdev linter`: Set `disallowed_html_tags` and `broken_site_link` detection in `high` severity to block future format issues

0.1.91
++++++
* `azdev generate-breaking-change-report`: Update report report template.

0.1.90
++++++
* `azdev cmdcov`: Fix incorrect detection of code changes as new commands

0.1.89
++++++
* `azdev scan/mask`: Add `--continue-on-failure` support

0.1.88
++++++
* `azdev cmdcov`: Fix incorrect detection of code changes as new commands

0.1.87
++++++
* `azdev linter`: Fix repo path failed when `detect_new_command`.

0.1.86
++++++
* `azdev linter`: Add close html tags into whitelist of `disallowed_html_tags`

0.1.85
++++++
* `azdev setup`: Setup the upstream and enable .githooks for azure-cli and azure-cli-extensions repos
* `azdev linter`: Add `disallowed_html_tags` and `broken_site_link` detection in linter rule and set them as `Medium` for unblock CI pipeline temporarily

0.1.84
++++++
* `azdev generate-breaking-change-report`: Fix `azdev -h` error caused by global importing `azure.cli.core` in `breaking-change.py` module.

0.1.83
++++++
* `azdev generate-breaking-change-report`: Fix `azdev.operations.breaking_change` not included in `setup.py`.

0.1.82
++++++
* `azdev generate-breaking-change-report`: New command to collect upcoming breaking changes from codebase.

0.1.81
++++++
* `azdev scan/mask`: Add `--confidence-level` to support secret pattern levels

0.1.80
++++++
* `azdev cmdcov`: Support both extension short name and long name
* `azdev cmdcov`: Fix sorting issues
* `azdev test`: Fix executable inconsistence in `subprocess` of windows platform

0.1.79
++++++
* Fix profile options

0.1.78
++++++
* Mitigate shell injection risk from user input.

0.1.77
++++++
* `azdev extension cal-next-version`: Fix pre_num when tagged preview version with `major`, `minor`, `patch`.

0.1.76
++++++
* `azdev extension cal-next-version`: Fix preview to stable version case.

0.1.75
++++++
* `azdev scan/mask`: Add `--include-pattern` and `--exclude-pattern` to support filtering files within directory

0.1.74
++++++
* `azdev scan/mask`: New commands for scanning and masking secrets for files or string

0.1.73
++++++
* `azdev command-change meta-export`: Add `has_completer` to denote whether completer is configed in arg
* `azdev command-change meta-export`: Extracting arg help and example for loaded HelpFiles

0.1.72
++++++
* Bump `pylint` to 3

0.1.71
++++++
* `azdev extension show`: Show detailed extension info that installed in your development environment.
* `azdev extension cal-next-version`: Fix last stable version parser from index.json.

0.1.70
++++++
* Fix cmdcov issue(#455): remove tested_command.txt reference.

0.1.69
++++++
* `azdev command-change tree-export`: Add command help message.

0.1.68
++++++
* `azdev command-change tree-export`: Add new command to support export command tree of CLI modules.

0.1.67
++++++
* `azdev extension cal-next-version`: Justify preview/exp tag operation based on last version's tag and next version's stable/preview tag.

0.1.66
++++++
* `azdev style`: Use azdev config files when .flake8 and pylintrc are not found in azure cli/ext repo.

0.1.65
++++++
* `azdev command-change meta-diff`: Add diff support for deprecate_info in subgroup, cmd, parameters and options.

0.1.64
++++++
* `azdev extension cal-next-version`: Fix module name when querying extension modules from index.

0.1.63
++++++
* `azdev`: Update required version for `azure-cli-diff-tool`.

0.1.62
++++++
* `azdev extension cal-next-version`: New command to calculate valid version for next extension module release.

0.1.61
++++++
* `azdev test`: Add some examples.
* `azdev style`: Modify the execution order of the _update_table function.
* `azdev linter`: Bug fixes for `_detected_tested_command`, strictly limited to starting with test and ending with .py or .yaml

0.1.60
++++++
* `azdev statistics list-command-table`: Handle exceptions when source code cannot be retrieved

0.1.59
++++++
* `azdev command-change meta-export`: Normalize basic cmd types: str, bool, int, float

0.1.58
++++++
* Fix cmdcov issue(#417): Any name of a parameter has been tested, the parameter should be considered as passing the parameter test coverage.

0.1.57
++++++
* `azdev command-change meta-diff`: Remove duplicated meta-diff code and use azure-cli-diff-tool

0.1.56
++++++
* Fix cmdcov issue(#410): Get config from github when get_cli_repo_path failed

0.1.55
++++++
* `azdev command-change meta-diff`: Fix data/meta_change_whitelist.txt pkg building

0.1.54
++++++
* `azdev command-change meta-export/meta-diff`: Add cmd `type` extraction, fix false positive in cmdPropUpdate and add whitelist in certain meta-changes (#401)

0.1.53
++++++
* `azdev command-change meta-export`: Add rule link (#402)

0.1.52
++++++
* Fix cmdcov issue(#396): Fix the regex which to get the command group

0.1.51
++++++
* Fix cmdcov issue(#391): Add violation message to cmdcov linter rule and fix related issues

0.1.50
++++++
* Fix cmdcov issue(#385): Add cmdcov to package data

0.1.49
++++++
* Add Command Coverage Report for CLI modules (#323)
* Add Linter rule missing_command_coverage and missing_parameter_coverage  (#323)
* Add Command Coverage Report for CLI extensions (#383)

0.1.48
++++++
* `azdev command-change meta-export`: Add option deprecation info and ignore `cmd` arg (#381)

0.1.47
++++++
* `azdev command-change meta-export`: Load parameter from module loader (#378)

0.1.46
++++++
* `azdev command-change meta-diff`: Add subgroups change detect (#374)

0.1.45
++++++
* `azdev command-change meta-diff`: Refine no meta diff output (#372)

0.1.44
++++++
* `azdev command-change meta-export`: Fix object dump failure (#370)

0.1.43
++++++
* `azdev statistics list-command-table`: Fix unexpected indent (#368)

0.1.42
++++++
* `azdev command-change meta-export/meta-diff`: Generate cli cmd meta data and the diffs between two meta data (#362)

0.1.41
++++++
* `azdev statistics list-command-table`: Support stats of nested function (#363)

0.1.40
++++++
* Fix pytest issues (#347)

0.1.39
++++++
* Fix package issues (#345)

0.1.38
++++++
* `azdev statistics list-command-table`: List Command table for CLI modules (#342)
* `azdev statistics diff-command-tables`: Diff the command table change (#343)

0.1.37
++++++
* `azdev verify license`: Support license for CodeGen V2 (#334)
* `azdev test`: Revert integrate pytest-cov  (#327)

0.1.36
++++++
* Remove colorama reference (#321)

0.1.35
++++++
* Support Python 3.10 (#319)
* Replace `master` branch by `main` branch (#315)
* Drop `mock` library (#313)
* Add extension repo missing error (#309)

0.1.34
++++++
* `azdev linter`: support to detect commmand groups which are missing in command_group_table (#308)

0.1.33
++++++
* Bump `pylint` to 2.8.2 and move `--ignore` to `pylintrc` file (#301)

0.1.32
++++++
* Bump `pylint` to 2.8.0 (#295)

0.1.31
++++++
* `azdev style`: Fix `pylint` by pinning `astroid` to 2.4.2 (#294)
* Fix `_copy_vendored_sdk` for Track 2 SDK (#293)

0.1.30
++++++
* Change azure-storage-blob dependency (#290)

0.1.29
++++++
* `azdev linter`: Remove the prefix dashes in option length calculation (#284)
* `azdev setup`: Show error if `pip` command fails (#281)
* Support Python 3.9 (#280)

0.1.28
++++++
* [Linter] Fix minor display issue in `azdev linter`.

0.1.27
++++++
* [Linter] "Show" command should use `show_command` or `custom_show_command`.

0.1.26
++++++
* Support PEP420 package

0.1.25
++++++
* `azdev test`: new parameter --mark
* Update the way invoking pytest
* `azdev perf benchmark`: refine output
* Support PEP420 package

0.1.24
++++++
* [Linter] Argument must have an option whose length is less than 22.
* [Linter] Argument cannot contain "`_`".

0.1.23
++++++
* [Linter] Only violation of high severity rule would exit with 1.
* Minimal pytest version requires at least 5.0.0.

0.1.22
++++++
* Hornor the configuration of pylint and flake8 in Azure/azure-cli and Azure/azure-cli-extensions.
* Rename test folder to make place for unittest of other commands.
* Enable test result coverage.

0.1.21
++++++
* Fix isort package version to 4.3.21.
* `azdev perf benchmark`: support new command to calculate each command execution time.

0.1.20
++++++
* `azdev setup`: Fix missing dependencies of azure-cli-testsdk

0.1.19
++++++
* Downgrade parameter_should_not_end_in_resource_group's severity to medium.
* Fix bug that azdev test could not work on Windows with Chinese system language.

0.1.18
++++++
* Linter Rule Severity: Rules now have an associated severity level. Only high severity rules should be run in CI. All previous rules are annotated as HIGH severity.

   * Note: HIGH severity rules are egregious and should generally be fixed, not excluded. LOW severity rules tend to be informational, and might raise false positives. Exclude them via `linter_exclusions.yml` in the CLI.

* `azdev linter`: Expose `--min-severity` to support idea of rule severity. New HIGH, MEDIUM and LOW severity rules have also been added.

0.1.17
++++++
* `azdev setup`: Add option --deps-from to allow resolving dependencies from requirements.txt or setup.py. The default changes to requirements.txt.

0.1.16
++++++
* `azdev test`: Add option --no-exit-first to disable pytest exit once failure is detected

0.1.15
++++++
* `sys.exit(0)` when no tests need to run instead of raising CLIError

0.1.14
++++++
* Refine the logic of testing against different profiles with `ProfileContext`
* pytest version limit change to pytest>=4.4.0
* Use `AzureDevOpsContext` to apply incremental test strategy
* Refine the main flow of azdev test to be more compact and clean

0.1.13
++++++
* azdev verify license: fix bug that license verification will omit files while checking extensions

0.1.12
++++++
* azdev extension publish: fix issue when --yes if not provided
* azdev verify license: support CodeGen generated License
* Drop Python 2 and Python 3.5 support

0.1.11
++++++
* azdev extension build: remove --universal to respect setup.cfg

0.1.10
++++++
* relax version limit of microsoft/Knack

0.1.9
++++++
* azdev extension publish: add --storage-account-key and remove --storage-subscription
* azdev extension update-index: remove unnecessary warning that will fail this command
* CI: use `pip install -e` instead in ADO to fix fix import bug

0.1.8
++++++
* fix: azdev test cannot be used in python 3.8.1 or later

0.1.7
++++++
* fix: azdev test cannot find core tests

0.1.6
++++++
* Fix bug: azdev==0.1.5 help commands' error

0.1.5
++++++
- azdev extension add/remove:
    - Add ability to supply wildcard (*) to install all available dev extensions.
    - Add ability to remove all installed dev extensions.
- azdev setup:
    - Add ability to install all extensions using `--ext/-e *`.
    - Add ability to install CLI edge build with `--cli/-c EDGE`.
- azdev style/test/linter:
    - Add special names CLI and EXT to allow running on just CLI modules or just extensions.
      extensions which have changed based on a git diff.
- azdev linter:
    - Added `--include-whl-extensions` flag to permit running the linter on extensions installed using
      the `az extension add` command.
- azdev verify license:
    - Command will not check any dev-installed CLI and extension repos. Previously, it only checked the CLI repo.
- New Command:
    - `azdev cli/extension generate-docs` to generate sphinx documentation.

0.1.4
++++++
* `azdev linter`: Fix issue with help example rule.
* `azdev style`: Omit namespace packages from core modules.
* `azdev verify document-map`: Updates to work correctly on Linux.

0.1.3
++++++
* `azdev linter`: Fix issue where certain installations would fail on `ci_exclusions.yml` not found.


0.1.2
++++++
* `azdev setup`: Fix regression where azure.cli could not be run after installation.

0.1.1
++++++
* `azdev cli/extension create`: Fix issue where supporting files were not included. Adjust generation logic.

0.1.0
++++++
* Update for compatability with azure-cli 2.0.68's new package structure.
* BREAKING CHANGE: Removed `azdev cli update-setup`. Package changes to azure-cli no longer require this.
* BREAKING CHANGE: `azdev verify history` and `azdev cli check-versions` no longer accept any arguments. Since there are
  now far fewer modules, these were deemed unnecessary.

0.0.6
++++++
* Added new commands `azdev cli create` and `azdev extension create` to scaffold new modules/extensions.
* `azdev setup`: Tweaks to interactive experience.
* `azdev test`: Fix issue where using `--profile` did not use the correct index.
                Changed the behavior to switch back to the original profile upon completion of tests.

0.0.5
++++++
* Fix issue where `azdev cli check-versions` did not accept the short form of a module name.
* Update `azdev cli check-versions` to allow modules as a positional argument, consistent with other azdev commands.
* Fix issue where `azdev test --discover` could result in a stack trace when a virtual environment exists within an extensions repo.

0.0.4
++++++
* Fix critical bug in `azdev setup`.

0.0.3
++++++
* Adds new commands `azdev extension build` and `azdev extension publish` to simplify extension publishing.
* Updates default exclusions for `azdev linter` when used on extensions.
* Adds a `--ci-exclusions` flag to `azdev linter` to emulate CI mode when run locally.
* Fix issue where `azdev test --discover` could result in a stack trace when a virtual environment exists within a cloned repo.
* Tweaks thresholds for `azdev per load-times`.

0.0.2
++++++

* Changes the behavior of `azdev test` to, by default, run tests on everything to be consistent with commands like `azdev style` and `azdev linter`.
* Removes `azdev verify version` and splits into two commands `azdev cli check-versions` and `azdev cli update-setup`.
* Various modifications to play nicely with azure-cli's CI build system.
* Revamps `azdev perf load-times` to reduce spurious failures.

0.0.1
++++++
* Initial release
