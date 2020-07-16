# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from knack.help_files import helps


helps[''] = """
    short-summary: Development utilities for Azure CLI 2.0.
"""


helps['setup'] = """
    short-summary: Set up your environment for development of Azure CLI command modules and/or extensions.
    examples:
        - name: Fully interactive setup (Must be run in an existing virtual environment).
          text: azdev setup

        - name: Install public CLI and setup an extensions repo (Must be run in an existing virtual environment).
          text: azdev setup -r azure-cli-extensions

        - name: Install CLI in the current virtual environment, along with the extensions repo. Will create a azure directory and config in the current virtual environment.
          text: azdev setup -c azure-cli -r azure-cli-extensions

        - name: Same as above but install the `alias` extension in the current virtual environment to.
          text: azdev setup -c azure-cli -r azure-cli-extensions -e alias

        - name: Same as above setup a new virtual environment, create a new azure directory and config in this new virtual environment
          text: azdev setup -c azure-cli -r azure-cli-extensions -s env1

        - name: Same as above, but do not setup new azure config in this virtual environment
          text: azdev setup -c azure-cli -r azure-cli-extensions -s env1 -g

        - name: Same as above but copy over system level azure settings into new virtual environment azure settings
          text: azdev setup -c azure-cli -r azure-cli-extensions -s env1 --copy

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
        - name: Run tests for specific modules.
          text: azdev test {mod1} {mod2}

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
    short-summary: Create a new Azure CLI extension.
    examples:
        - name: Generate a new CLI extension named 'contoso' with local or remote azure-rest-api-specs repo.
          text: >
            azdev extension create contoso --azure-rest-api-specs {azure-rest-api-specs repo path}
        - name: Generate a new CLI extension named 'contoso' with the default azure-rest-api-specs repo.
          text: >
            azdev extension create contoso
        - name: Generate a new CLI extension named 'contoso' with specified autorest.az release.
          text: >
            azdev extension create contoso --use=https://github.com/Azure/autorest.az/releases/download/1.4.0/autorest-az-1.4.0.tgz
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
