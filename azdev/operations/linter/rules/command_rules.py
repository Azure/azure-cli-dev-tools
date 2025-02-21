# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------
# pylint: disable=duplicate-code

from azdev.operations.constant import DISALLOWED_HTML_TAG_RULE_LINK
from ..rule_decorators import CommandRule
from ..linter import RuleError, LinterSeverity
from ..util import has_illegal_html_tag, has_broken_site_links


@CommandRule(LinterSeverity.HIGH)
def missing_command_help(linter, command_name):
    if not linter.get_command_help(command_name) and not linter.command_expired(command_name):
        raise RuleError('Missing help')


@CommandRule(LinterSeverity.HIGH)
def no_ids_for_list_commands(linter, command_name):
    if command_name.split()[-1] == 'list' and 'ids' in linter.get_command_parameters(command_name):
        raise RuleError('List commands should not expose --ids argument')


@CommandRule(LinterSeverity.HIGH)
def expired_command(linter, command_name):
    if linter.command_expired(command_name):
        raise RuleError('Deprecated command is expired and should be removed.')


@CommandRule(LinterSeverity.LOW)
def group_delete_commands_should_confirm(linter, command_name):
    # We cannot detect from cmd table etc whether a delete command deletes a collection, group or set of resources.
    # so warn users for every delete command.

    if command_name.split()[-1].lower() == "delete":
        if 'yes' not in linter.get_command_parameters(command_name):
            raise RuleError("If this command deletes a collection, or group of resources. "
                            "Please make sure to ask for confirmation.")


@CommandRule(LinterSeverity.HIGH)
def disallowed_html_tag_from_command(linter, command_name):
    if command_name == '' or not linter.get_loaded_help_entry(command_name):
        return
    help_entry = linter.get_loaded_help_entry(command_name)
    if help_entry.short_summary and (disallowed_tags := has_illegal_html_tag(help_entry.short_summary,
                                                                             linter.diffed_lines)):
        raise RuleError("Disallowed html tags {} in short summary. "
                        "If the content is a placeholder, please remove <> or wrap it with backtick. "
                        "For example: 1) <Name>-res.yaml -> `<Name>-res.yaml`; "
                        "2) http://<URL>:<PORT> -> `http://<URL>:<PORT>`. "
                        "For more info please refer to: {}".format(disallowed_tags,
                                                                   DISALLOWED_HTML_TAG_RULE_LINK))
    if help_entry.long_summary and (disallowed_tags := has_illegal_html_tag(help_entry.long_summary,
                                                                            linter.diffed_lines)):
        raise RuleError("Disallowed html tags {} in long summary. "
                        "If content is a placeholder, please remove <> or wrap it with backtick. "
                        "For example: 1) <Name>-res.yaml -> `<Name>-res.yaml`; "
                        "2) http://<URL>:<PORT> -> `http://<URL>:<PORT>`. "
                        "For more info please refer to: {}".format(disallowed_tags,
                                                                   DISALLOWED_HTML_TAG_RULE_LINK))


@CommandRule(LinterSeverity.MEDIUM)
def broken_site_link_from_command(linter, command_name):
    if command_name == '' or not linter.get_loaded_help_entry(command_name):
        return
    help_entry = linter.get_loaded_help_entry(command_name)
    if help_entry.short_summary and (broken_links := has_broken_site_links(help_entry.short_summary,
                                                                           linter.diffed_lines)):
        raise RuleError("Broken links {} in short summary. "
                        "If link is an example, please wrap it with backtick. ".format(broken_links))
    if help_entry.long_summary and (broken_links := has_broken_site_links(help_entry.long_summary,
                                                                          linter.diffed_lines)):
        raise RuleError("Broken links {} in long summary. "
                        "If link is an example, please wrap it with backtick. ".format(broken_links))
