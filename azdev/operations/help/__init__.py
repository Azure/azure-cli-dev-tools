# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from __future__ import print_function

import os
import json

from knack.util import CLIError
from knack.log import get_logger

from azdev.utilities import (
    display, heading, subheading,
    get_cli_repo_path, get_path_table
)

from azdev.utilities.tools import require_azure_cli
from azure.cli.core.extension.operations import add_extension, remove_extension, list_available_extensions

DOC_MAP_NAME = 'doc_source_map.json'
HELP_FILE_NAME = '_help.py'
DOC_SOURCE_MAP_PATH = os.path.join('doc', 'sphinx', 'azhelpgen', DOC_MAP_NAME)

_logger = get_logger(__name__)


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
        help_path = help_path.replace(cli_repo.lower() + '\\', '')
        if help_path in help_files_in_map:
            continue
        not_in_map.append(help_path)
    return not_in_map

def generate_ref_docs(generate_for_extensions=None, output_dir=None, output_type=None):
    import tempfile

    heading('Generate Reference Docs')

    # require that azure cli installed
    require_azure_cli()

    # handle output_dir
    # if non specified, store in "_build" in the current working directory
    if not output_dir:
        output_dir = tempfile.mkdtemp(prefix="doc_output_")

    # ensure output_dir exists otherwise create it
    output_dir = os.path.abspath(output_dir)
    if not os.path.exists(output_dir):
        existing_path = os.path.dirname(output_dir)
        base_dir = os.path.basename(output_dir)
        if not os.path.exists(existing_path):
            raise CLIError("Cannot create output directory {} in non-existent path {}."
                           .format(base_dir, existing_path))

        os.mkdir(output_dir)

    display("Docs will be placed in {}.".format(output_dir))

    if generate_for_extensions:
        public_extensions = list_available_extensions()
        if not public_extensions:
            raise CLIError("Failed to retrieve public extensions.")

        for extension in public_extensions:
            add_extension()
            # generate documentation for installed extensions
            _call_sphinx_build(output_type, output_dir, for_extensions_alone=True)

    else:
        # Generate documentation for all comamnds
        _call_sphinx_build(output_type, output_dir)
        display("Reference docs have been generated in {}".format(output_dir))


def _call_sphinx_build(builder_name, output_dir, for_extensions_alone=False):
    import sys
    from subprocess import check_call, CalledProcessError

    conf_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'refdoc')

    if for_extensions_alone:
        source_dir = os.path.abspath(os.path.join(conf_dir, 'extension_docs'))
    else:
        source_dir = os.path.abspath(os.path.join(conf_dir, 'cli_docs'))

    try:
        sphinx_cmd = ['sphinx-build', '-b', builder_name, '-c', conf_dir, source_dir, output_dir]
        _logger.info("sphinx cmd: %s", " ".join(sphinx_cmd))
        check_call(sphinx_cmd, stdout=sys.stdout, stderr=sys.stderr)
    except CalledProcessError:
        raise CLIError("Doc generation failed.")
