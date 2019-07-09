# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azdev.operations.help.refdoc.common.directives import AbstractHelpGenDirective
from azdev.operations.help.refdoc.common.directives import setup_common_directives

from knack.log import get_logger
from knack.help import GroupHelpFile

from azure.cli.core.file_util import _store_parsers, _is_group
from azure.cli.core.commands import ExtensionCommandSource
from azure.cli.core._help import CliCommandHelpFile

logger = get_logger(__name__)

class ExtensionHelpGenDirective(AbstractHelpGenDirective):
    """
        CLI Extensions Sphinx Directive
        Ensure that sphinx output is generated from only extension help files
    """

    def _get_help_files(self, az_cli):
        return get_extension_help_files(az_cli)

    def _load_doc_source_map(self):
        # no doc source map for extensions
        pass

    def _get_doc_source_content(self, doc_source_map, help_file):
        # no doc source map for extensions
        pass

# TODO: move this into core
def get_extension_help_files(cli_ctx):

    # 1. Create invoker and load command table and arguments. Remember to turn off applicability check.
    invoker = cli_ctx.invocation_cls(cli_ctx=cli_ctx, commands_loader_cls=cli_ctx.commands_loader_cls,
                                     parser_cls=cli_ctx.parser_cls, help_cls=cli_ctx.help_cls)
    cli_ctx.invocation = invoker

    invoker.commands_loader.skip_applicability = True
    cmd_table = invoker.commands_loader.load_command_table(None)

    #   turn off applicability check for all loaders
    for loaders in invoker.commands_loader.cmd_to_loader_map.values():
        for loader in loaders:
            loader.skip_applicability = True

    #   filter the command table to only get commands from extensions
    cmd_table = {k: v for k, v in cmd_table.items() if isinstance(v.command_source, ExtensionCommandSource)}
    invoker.commands_loader.command_table = cmd_table
    logger.warning('Found {} command(s) from the extension.\n'.format(len(cmd_table)))

    for cmd_name in cmd_table:
        invoker.commands_loader.load_arguments(cmd_name)

    invoker.parser.load_command_table(invoker.commands_loader)

    # 2. Now load applicable help files
    parser_keys = []
    parser_values = []
    sub_parser_keys = []
    sub_parser_values = []
    _store_parsers(invoker.parser, parser_keys, parser_values, sub_parser_keys, sub_parser_values)
    for cmd, parser in zip(parser_keys, parser_values):
        if cmd not in sub_parser_keys:
            sub_parser_keys.append(cmd)
            sub_parser_values.append(parser)
    help_ctx = cli_ctx.help_cls(cli_ctx=cli_ctx)
    help_files = []
    for cmd, parser in zip(sub_parser_keys, sub_parser_values):
        try:
            help_file = GroupHelpFile(help_ctx, cmd, parser) if _is_group(parser) \
                else CliCommandHelpFile(help_ctx, cmd, parser)
            help_file.load(parser)
            help_files.append(help_file)
        except Exception as ex:
            print("Skipped '{}' due to '{}'".format(cmd, ex))
    help_files = sorted(help_files, key=lambda x: x.command)
    logger.warning('Generated {} help objects from the extension.\n'.format(len(help_files)))
    return help_files

def setup(app):
    """ Setup sphinx app with help generation directive. This is called by sphinx.
    :param app: The sphinx app
    :return:
    """
    app.add_directive('exthelpgen', ExtensionHelpGenDirective)
    setup_common_directives(app)
