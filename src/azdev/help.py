# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from knack.help_files import helps  # pylint: disable=unused-import


helps[''] = """
    short-summary: Development utilities for Azure CLI 2.0.
"""


helps['setup'] = """
    short-summary: Set up your environment for development of Azure CLI command modules and/or extensions.
"""


helps['configure'] = """
    short-summary: Configure `azdev` for development.
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


helps['verify version'] = """
    short-summary: Verify package versions.
"""


helps['load-all'] = """
    short-summary: Load the full command table, command arguments and help.
"""


helps['style'] = """
    short-summary: Check code style (pylint and PEP8).
"""


helps['test'] = """
    short-summary: Record or reply CLI tests.
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


helps['perf load-time'] = """
    short-summary: Verify that all modules load within an acceptable timeframe.
"""


helps['sdk'] = """
    short-summary: Perform quick Python SDK operations.
"""


helps['sdk draft'] = """
    short-summary: Install draft packages from the Python SDK repo.
"""