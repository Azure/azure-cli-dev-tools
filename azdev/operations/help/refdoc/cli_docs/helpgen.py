# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import json

from azdev.utilities import get_cli_repo_path
from azdev.operations.help import DOC_SOURCE_MAP_PATH
from azdev.operations.help.refdoc.common.directives import AbstractHelpGenDirective
from azdev.operations.help.refdoc.common.directives import setup_common_directives

from azure.cli.core._help import CliCommandHelpFile  # pylint: disable=import-error
from azure.cli.core.file_util import create_invoker_and_load_cmds_and_args, get_all_help  # pylint: disable=import-error

class HelpGenDirective(AbstractHelpGenDirective):
    """ General CLI Sphinx Directive
        The Core CLI has a doc source map to determine help text source for core cli commands. Extension help processed
        here will have no doc source
    """

    def _get_help_files(self, az_cli):
        create_invoker_and_load_cmds_and_args(az_cli)
        return get_all_help(az_cli)

    def _load_doc_source_map(self):
        map_path = os.path.join(get_cli_repo_path(), DOC_SOURCE_MAP_PATH)
        with open(map_path) as open_file:
            return json.load(open_file)

    def _get_doc_source_content(self, doc_source_map, help_file):
        is_command = isinstance(help_file, CliCommandHelpFile)
        result = None
        if not is_command:
            top_group_name = help_file.command.split()[0] if help_file.command else 'az'
            doc_source_value = doc_source_map[top_group_name] if top_group_name in doc_source_map else ''
            result = '{}:docsource: {}'.format(self._INDENT, doc_source_value)
        else:
            top_command_name = help_file.command.split()[0] if help_file.command else ''
            if top_command_name in doc_source_map:
                result = '{}:docsource: {}'.format(self._INDENT, doc_source_map[top_command_name])
        return result

def setup(app):
    """ Setup sphinx app with help generation directive. This is called by sphinx.
    :param app: The sphinx app
    :return:
    """
    app.add_directive('corehelpgen', HelpGenDirective)
    setup_common_directives(app)
