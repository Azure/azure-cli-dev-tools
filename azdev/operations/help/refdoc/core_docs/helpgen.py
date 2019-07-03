# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import json

from azdev.operations.help.refdoc.common.directives import AbstractHelpGenDirective
from azdev.operations.help.refdoc.common.directives import setup_common_directives

from azure.cli.core._help import CliCommandHelpFile
from azure.cli.core.file_util import create_invoker_and_load_cmds_and_args, get_all_help

class CoreHelpGenDirective(AbstractHelpGenDirective):
    """ Core CLI Sphinx Directive
        The Core CLI has a doc source map to determine help text source for commands
    """

    def _get_help_files(self, az_cli):
        create_invoker_and_load_cmds_and_args(az_cli)
        return get_all_help(az_cli)

    def _load_doc_source_map(self):
        doc_source_map_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(doc_source_map_dir, 'doc_source_map.json')) as open_file:
            return json.load(open_file)

    def _yield_doc_source(self, doc_source_map, help_file):
        is_command = isinstance(help_file, CliCommandHelpFile)
        if not is_command:
            top_group_name = help_file.command.split()[0] if help_file.command else 'az'
            yield '{}:docsource: {}'.format(self._INDENT,
                                            doc_source_map[top_group_name] if top_group_name in doc_source_map else '')
        else:
            top_command_name = help_file.command.split()[0] if help_file.command else ''
            if top_command_name in doc_source_map:
                yield '{}:docsource: {}'.format(self._INDENT, doc_source_map[top_command_name])
        yield ''


def setup(app):
    """ Setup sphinx app with help generation directive. This is called by sphinx.
    :param app: The sphinx app
    :return:
    """
    app.add_directive('corehelpgen', CoreHelpGenDirective)
    setup_common_directives(app)