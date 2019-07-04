# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from __future__ import print_function

import os
import json

from knack.util import CLIError

from azdev.utilities import (
    display, heading, subheading,
    get_cli_repo_path, get_path_table
)

DOC_MAP_NAME = 'doc_source_map.json'
HELP_FILE_NAME = '_help.py'
DOC_SOURCE_MAP_PATH = os.path.join('doc', 'sphinx', 'azhelpgen', DOC_MAP_NAME)


def check_document_map():

    heading('Verify Document Map')

    cli_repo = get_cli_repo_path()

    map_path = os.path.join(cli_repo, DOC_SOURCE_MAP_PATH)
    help_files_in_map = _get_help_files_in_map(map_path)
    help_files_not_found = _map_help_files_not_found(cli_repo, help_files_in_map)
    help_files_to_add_to_map = _help_files_not_in_map(cli_repo, help_files_in_map)

    subheading('Results')
    if help_files_not_found or help_files_to_add_to_map:
        error_lines = []
        error_lines.append('Errors whilst verifying {}!'.format(DOC_MAP_NAME))
        if help_files_not_found:
            error_lines.append('The following files are in {} but do not exist:'.format(DOC_MAP_NAME))
            error_lines += help_files_not_found
        if help_files_to_add_to_map:
            error_lines.append('The following files should be added to {}:'.format(DOC_MAP_NAME))
            error_lines += help_files_to_add_to_map
        error_msg = '\n'.join(error_lines)
        raise CLIError(error_msg)
    display('Verified {} OK.'.format(DOC_MAP_NAME))


def _get_help_files_in_map(map_path):
    with open(map_path) as json_file:
        json_data = json.load(json_file)
        return [os.path.normpath(x) for x in list(json_data.values())]


def _map_help_files_not_found(cli_repo, help_files_in_map):
    missing_files = []
    for path in help_files_in_map:
        if not os.path.isfile(os.path.normpath(os.path.join(cli_repo, path))):
            missing_files.append(path)
    return missing_files


def _help_files_not_in_map(cli_repo, help_files_in_map):
    not_in_map = []
    for _, path in get_path_table()['mod'].items():
        help_path = os.path.join(path, HELP_FILE_NAME)
        help_path = help_path.replace(cli_repo.lower() + os.sep, '')
        if help_path in help_files_in_map or not os.path.isfile(help_path):
            continue
        not_in_map.append(help_path)
    return not_in_map
