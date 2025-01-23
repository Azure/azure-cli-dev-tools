# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from knack.help_files import helps
# pylint: disable=line-too-long, anomalous-backslash-in-string


helps[''] = """
    short-summary: Development utilities for Azure CLI 2.0.
"""


helps['setup'] = """
    short-summary: Set up your environment for development of Azure CLI command modules and/or extensions.
    long-summary: Use --verbose to show the commands that are run, --debug to show the command output.
    examples:
        - name: Fully interactive setup.
          text: azdev setup

        - name: Install only the CLI in dev mode and search for the existing repo.
          text: azdev setup -c

        - name: Install public CLI and setup an extensions repo. Do not install any extensions.
          text: azdev setup -r azure-cli-extensions

        - name: Install CLI in dev mode, along with the extensions repo. Auto-find the CLI repo and install the `alias` extension in dev mode.
          text: azdev setup -c -r azure-cli-extensions -e alias

        - name: Install only the CLI in dev mode and resolve dependencies from setup.py.
          text: azdev setup -c -d setup.py
"""


helps['cli'] = """
    short-summary: Commands for working with CLI modules.
"""

helps['cli check-versions'] = """
    short-summary: Verify package versions against those hosted on PyPI.
    long-summary: >
        This is used to ensure the correct module versions are bumped prior to release.
    examples:
        - name: Verify all versions and audit them against PyPI.
          text: azdev cli check-versions
"""

helps['cli create'] = """
    short-summary: Create a new Azure CLI module template.
    examples:
        - name: Scaffold a new CLI module named 'contoso'.
          text: azdev cli create contoso
        - name: Scaffold a new CLI module with the azure-mgmt-contoso SDK.
          text: >
            azdev cli create contoso --required-sdk azure-mgmt-contoso==0.1.0 --operation-name ContosoOperations
            --client-name ContosoManagementClient --sdk-property contoso_name
"""


helps['cli generate-docs'] = """
    short-summary: >
       Generate reference docs for CLI commands.
"""


helps['configure'] = """
    short-summary: Configure azdev for use without installing anything.
"""


helps['verify'] = """
    short-summary: Verify CLI product features.
"""


helps['verify license'] = """
    short-summary: Verify license headers.
"""


helps['verify document-map'] = """
    short-summary: Verify documentation map.
"""


helps['verify default-modules'] = """
    short-summary: Verify default modules.
"""


helps['verify package'] = """
    short-summary: Verify the basic requirements for command module packages.
"""


helps['verify history'] = """
    short-summary: Verify the README and HISTORY files for each module so they format correctly on PyPI.
"""


helps['style'] = """
    short-summary: Check code style (pylint and PEP8).
    examples:
        - name: Check style for only those modules which have changed based on a git diff.
          text: azdev style --repo azure-cli --tgt upstream/master --src upstream/dev
"""


helps['test'] = """
    short-summary: Record or replay CLI tests.
    parameters:
        - name: --pytest-args -a
          populator-commands:
            - pytest -h
    examples:
        - name: Run all tests.
          text: azdev test

        - name: Run tests for main modules.
          text: azdev test CLI

        - name: Run tests for extensions.
          text: azdev test EXT

        - name: Run tests for specific modules.
          text: azdev test {mod1} {mod2}

        - name: Run tests for specific cli modules, it is recommended to use the long name azure-cli-{mod}.
          text: azdev test azure-cli-vm azure-cli-compute

        - name: Run tests for specific extensions, it is recommended to use the long name azext_{ext}.
          text: azdev test azext_containerapp azext_aosm

        - name: Run tests for specific test files.
          text: azdev test test_account_scenario

        - name: Run tests for specific python class.
          text: azdev test SubscriptionClientScenarioTest

        - name: Run tests for specific test cases.
          text: azdev test test_account

        - name: Re-run the tests that failed the previous run.
          text: azdev test --lf

        - name: Run tests for a module but run the tests that failed last time first.
          text: azdev test {mod} -a --ff

        - name: Run tests for only those modules which have changed based on a git diff.
          text: azdev test --repo azure-cli --tgt upstream/master --src upstream/dev
"""


helps['linter'] = """
    short-summary: Static code checks of the CLI command table.
    examples:
        - name: Check linter rules for only those modules which have changed based on a git diff.
          text: azdev linter --repo azure-cli --tgt upstream/master --src upstream/dev
"""

helps['scan'] = r"""
    short-summary: Scan secrets for files or string
    long-summary: Check built-in scanning rules at https://github.com/microsoft/security-utilities/blob/main/GeneratedRegexPatterns/PreciselyClassifiedSecurityKeys.json
    examples:
        - name: Scan secrets for a single file with custom patterns
          text: |
                azdev scan --file-path my_file.yaml --custom-pattern my_pattern.json
                ("my_pattern.json" contains the following content)
                {
                    "Include": [
                        {
                            "Pattern": "(?<refine>[\w.%#+-]+)(%40|@)([a-z0-9.-]*.[a-z]{2,})",
                            "Name": "EmailAddress",
                            "Signatures": ["%40", "@"]
                        },
                        {
                            "Pattern": "(?<refine>[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12})",
                            "Name": "GUID"
                        }
                    ],
                    "Exclude": [
                        {
                            "Id": "SEC101/156",
                            "Name": "AadClientAppIdentifiableCredentials",
                        }
                    ]
                }
        - name: Scan secrets for raw string and save results to file
          text: |
                azdev scan --data "my string waiting to be scanned" --save-scan-result True
        - name: Recursively scan secrets for a directory and save results to specific file
          text: |
                azdev scan --directory-path /path/to/my/folder --recursive --scan-result-path /path/to/scan_result.json
        - name: Scan secrets for all json files and yaml files within a directory
          text: |
                azdev scan --directory-path /path/to/my/folder --include-pattern *.yaml *.json
"""

helps['mask'] = """
    short-summary: Mask secrets for files or string
    long-summary: |
                Redaction type 'FIXED_VALUE' will mask all secrets with '***'.
                Redaction type 'FIXED_LENGTH' will mask secrets with several '*'s which will keep the original secret length.
                Redaction type 'SECRET_NAME' redaction type will mask secrets with their secret name (type).
                Redaction type 'CUSTOM' will mask secrets with 'redaction_token' value you specify through saved scan result file.
                Check built-in scanning rules at https://github.com/microsoft/security-utilities/blob/main/GeneratedRegexPatterns/PreciselyClassifiedSecurityKeys.json
"""

helps['statistics'] = """
    short-summary: Commands for CLI modules statistics.
"""

helps['statistics list-command-table'] = """
    short-summary: List Command table for CLI module.
    examples:
        - name: List command table for the network module
          text: azdev statistics list-command-table network -o table
        - name: List command table for all modules of azure-cli repo, without commands details
          text: azdev statistics list-command-table CLI --statistics-only
"""

helps['statistics diff-command-tables'] = """
    short-summary: Diff the command table change.
    examples:
        - name: Diff the command table change from May to Oct
          text: azdev statistics diff-command-tables --table-path command-table_May_01.json --diff-table-path command-table_Oct_01.json --statistics-only
"""

helps['command-change'] = """
    short-summary: Commands for CLI modules meta data.
"""

helps['command-change meta-export'] = """
    short-summary: Export Command meta data for CLI module.
    examples:
        - name: Export command meta for the monitor and network module
          text: azdev command-change meta-export network monitor -o table
"""

helps['command-change meta-diff'] = """
    short-summary: Diff the command meta between provided meta files.
    examples:
        - name: Diff the command meta change from fileA to fileB
          text: azdev command-change meta-diff --base-meta-file fileA --diff-meta-file fileB --only-break
"""

helps['command-change tree-export'] = """
    short-summary: Export Command Tree for CLI modules or extensions.
    examples:
        - name: Export command tree for CLI modules
          text: azdev command-change tree-export CLI --output-file command_tree.json
"""

helps['perf'] = """
    short-summary: Commands to test CLI performance.
"""


helps['perf load-times'] = """
    short-summary: Verify that all modules load within an acceptable timeframe.
"""

helps['perf benchmark'] = """
    short-summary: Display benchmark staticstic of Azure CLI (Extensions) commands via execute it with "python -m azure.cli {COMMAND}" in a separate process.
    examples:
        - name: Run benchmark on "network application-gateway" and "storage account"
          text: azdev perf benchmark "network application-gateway -h" "storage account" "version" "group list"
"""

helps['extension'] = """
    short-summary: Control which CLI extensions are visible in the development environment.
"""


helps['extension create'] = """
    short-summary: Create a new Azure CLI extension template.
    examples:
        - name: Scaffold a new CLI extension named 'contoso'.
          text: azdev extension create contoso
        - name: Scaffold a new CLI extension with the azure-mgmt-contoso SDK.
          text: >
            azdev extension create contoso --local-sdk {sdkPath} --operation-name ContosoOperations
            --client-name ContosoManagementClient --sdk-property contoso_name
"""


helps['extension add'] = """
    short-summary: Make an extension visible to the development environment.
    long-summary: The source code for the extension must already be on your machine.
"""


helps['extension build'] = """
    short-summary: Construct a WHL file for one or more extensions.
"""


helps['extension remove'] = """
    short-summary: Make an extension no longer visible to the development environment.
    long-summary: This does not remove the extensions source code from your machine.
"""


helps['extension list'] = """
    short-summary: List what extensions are currently visible to your development environment.
"""

helps['extension show'] = """
    short-summary: Show detailed extension info that installed in your development environment.
"""

helps['extension publish'] = """
    short-summary: Build and publish an extension to a storage account.
    long-summary: Storage parameters may be persisted in the [defaults] section of your config file for convenience.
    examples:
        - name: Publish the contoso extension to a storage account and update the index. This will then be ready for a PR.
          text: >
            azdev extension publish contoso --update-index --storage-account mystorage --storage-account-key 0000-0000 --storage-container extensions
"""


helps['extension update-index'] = """
    short-summary: Update the extensions index.json from a built WHL file.
"""

helps['extension cal-next-version'] = """
    short-summary: Calculate valid version for next extension module release.
"""

helps['extension repo'] = """
    short-summary: Commands to manage extension repositories for development.
    long-summary: >
        Extensions installed via the `az extension` commands are located in a specific
        folder. This folder is not well-suited for development. The CLI will look for
        in-development extensions in any number of Git repositories. These commands are
        used to add and remove repositories from the list of locations the CLI will search
        when looking for in-development extensions.
"""


helps['extension repo add'] = """
    short-summary: Add an extension repository to search for in-development extensions.
"""


helps['extension repo remove'] = """
    short-summary: >
        Remove a repository from the list of places to search for in-development extensions.
    long-summary: >
        This will not remove the extension repository from your system, but will appear to
        have the effect of uninstalling any extensions that were previously installed from
        that repository.
"""


helps['extension repo list'] = """
    short-summary: >
        List the repositories that will be searched for in-development extensions.
"""

helps['extension generate-docs'] = """
    short-summary: >
       Generate reference docs for CLI extensions commands.
    long-summary: >
        This command installs the extensions in a temporary directory and sets it as the extensions dir when generating reference docs.
"""

helps['cmdcov'] = """
    short-summary: Run command test coverage and generate CLI command test coverage report.
    examples:
        - name: Check all CLI modules command test coverage.
          text: azdev cmdcov CLI
        - name: Check one or serveral modules command test coverage.
          text: azdev cmdcov vm storage
        - name: Check CLI modules command test coverage in argument level.
          text: azdev cmdcov CLI --level argument
"""

helps['generate-breaking-change-report'] = """
    short-summary: Collect pre-announced breaking changes items and generate the report.
    examples:
        - name: Collect all pre-announced breaking changes, including any that did not specify a target version and group them by target version.
          text: azdev generate-breaking-change-report CLI --group-by-version --target-version None
        - name: Collect all pre-announced breaking changes target before next breaking change window, and display them in markdown.
          text: azdev generate-breaking-change-report CLI --output-format markdown
        - name: Collect all pre-announced breaking changes in vm, including those failed to specify a target version, and display them in json
          text: azdev generate-breaking-change-report vm --target-version None
"""
