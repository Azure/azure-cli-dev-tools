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
        - name: Fully interactive setup.
          text: azdev setup

        - name: Install only the CLI in dev mode and search for the existing repo.
          text: azdev setup -c

        - name: Install public CLI and setup an extensions repo. Do not install any extensions.
          text: azdev setup -r azure-cli-extensions

        - name: Install CLI in dev mode, along with the extensions repo. Auto-find the CLI repo and install the `alias` extension in dev mode.
          text: azdev setup -c -r azure-cli-extensions -e alias
"""


helps['cli'] = """
    short-summary: Commands for working with CLI modules.
"""

helps['cli check-versions'] = """
    short-summary: Verify package versions against those hosted on PyPI and/or in the azure-cli setup.py file.
    long-summary: >
        This is used to ensure the correct module versions are bumped prior to release.
    examples:
        - name: Verify all versions and audit them against azure-cli's setup.py ONLY.
          text: azdev cli check-versions

        - name: Verify all versions and update azure-cli's setup.py with each module's verison.
          text: azdev cli check-versions --update --pin
"""

helps['cli update-setup'] = """
    short-summary: Update the azure-cli setup.py file.
    examples:
        - name: Update azure-cli's setup.py with unpinned module verions.
          text: azdev cli update-setup

        - name: Update azure-cli's setup.py with pinned module versions.
          text: azdev cli update-setup --pin
"""


helps['configure'] = """
    short-summary: Configure azdev for use without installing anything.
"""


helps['coverage'] = """
    short-summary: Test coverage statistics and reports.
"""


helps['coverage code'] = """
    short-summary: Run CLI tests with code coverage.
"""


helps['coverage command'] = """
    short-summary: Analyze CLI test run data for command and argument coverage.
    long-summary: This does not run any tests!
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
"""


helps['test'] = """
    short-summary: Record or replay CLI tests.
    parameters:
        - name: --pytest-args -a
          populator-commands:
            - pytest -h
    examples:
        - name: Run all tests.
          text: azdev test --ci

        - name: Run tests for specific modules.
          text: azdev test {mod1} {mod2}

        - name: Re-run the tests that failed the previous run.
          text: azdev test --lf

        - name: Run tests for a module but run the tests that failed last time first.
          text: azdev test {mod} -a --ff
"""


helps['linter'] = """
    short-summary: Static code checks of the CLI command table.
"""


helps['perf'] = """
    short-summary: Commands to test CLI performance.
"""


helps['perf load-times'] = """
    short-summary: Verify that all modules load within an acceptable timeframe.
"""


helps['sdk'] = """
    short-summary: Perform quick Python SDK operations.
"""


helps['sdk draft'] = """
    short-summary: Install draft packages from the Python SDK repo.
"""


helps['extension'] = """
    short-summary: Control which CLI extensions are visible in the development environment.
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


helps['group'] = """
    short-summary: Convenience commands to manage Azure resource groups.
"""


helps['group delete'] = """
    short-summary: Delete several resource groups with filters. Useful for cleaning up test resources.
    long-summary: >
        Can filter either by key tags used by the CLI infrastructure, or by name prefix. If name prefix
        is used, the tag filters will be ignored. This command doesn't guarantee the resource group will
        be deleted.
"""
