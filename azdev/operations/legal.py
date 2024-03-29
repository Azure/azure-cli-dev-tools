# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import pathlib

from knack.util import CLIError

from azdev.utilities import (
    display, heading, subheading, get_cli_repo_path, get_ext_repo_paths)


LICENSE_HEADER = """# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
"""

WRAPPED_LICENSE_HEADER = """# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
"""


_IGNORE_SUBDIRS = ['__pycache__', 'vendored_sdks', 'site-packages', 'env']


def check_license_headers():

    heading('Verify License Headers')

    cli_path = get_cli_repo_path()
    all_paths = [cli_path]
    for path in get_ext_repo_paths():
        all_paths.append(path)

    files_without_header = []
    for path in all_paths:
        py_files = pathlib.Path(path).glob('**' + os.path.sep + '*.py')

        for py_file in py_files:
            py_file = str(py_file)

            if py_file.endswith('azure_cli_bdist_wheel.py'):
                continue

            for ignore_token in _IGNORE_SUBDIRS:
                if ignore_token in py_file:
                    break
            else:
                with open(str(py_file), 'r', encoding='utf-8') as f:
                    file_text = f.read()

                    if not file_text:
                        continue

                    test_results = [
                        LICENSE_HEADER in file_text,
                        WRAPPED_LICENSE_HEADER in file_text
                    ]
                    if not any(test_results):
                        files_without_header.append(py_file)

    subheading('Results')
    if files_without_header:
        raise CLIError("{}\nError: {} files don't have the required license headers.".format(
            '\n'.join(files_without_header), len(files_without_header)))
    display('License headers verified OK.')
