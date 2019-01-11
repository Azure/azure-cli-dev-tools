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
    get_cli_repo_path, get_path_table,
    COMMAND_MODULE_PREFIX
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
    hep_files_to_add_to_map = _help_files_not_in_map(cli_repo, help_files_in_map)

    subheading('Results')
    if help_files_not_found or hep_files_to_add_to_map:
        error_lines = []
        error_lines.append('Errors whilst verifying {}!'.format(DOC_MAP_NAME))
        if help_files_not_found:
            error_lines.append('The following files are in {} but do not exist:'.format(DOC_MAP_NAME))
            error_lines += help_files_not_found
        if hep_files_to_add_to_map:
            error_lines.append('The following files should be added to {}:'.format(DOC_MAP_NAME))
            error_lines += hep_files_to_add_to_map
        error_msg = '\n'.join(error_lines)
        raise CLIError(error_msg)
    display('Verified {} OK.'.format(DOC_MAP_NAME))


def _get_help_files_in_map(map_path):
    with open(map_path) as json_file:
        json_data = json.load(json_file)
        return list(json_data.values())


def _map_help_files_not_found(cli_repo, help_files_in_map):
    none_existent_files = []
    for f in help_files_in_map:
        if not os.path.isfile(os.path.join(cli_repo, f)):
            none_existent_files.append(f)
    return none_existent_files


def _help_files_not_in_map(cli_repo, help_files_in_map):
    found_files = []
    not_in_map = []
    for name, path in get_path_table()['mod'].items():
        name.replace(COMMAND_MODULE_PREFIX, '')
        help_file = os.path.join(path, 'azure', 'cli', 'command_modules', name, HELP_FILE_NAME)
        if os.path.isfile(help_file):
            found_files.append(help_file)
    for f in found_files:
        f_path = f.replace(cli_repo + '/', '')
        if f_path not in help_files_in_map:
            not_in_map.append(f_path)
    return not_in_map
