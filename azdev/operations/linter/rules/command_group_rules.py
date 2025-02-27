# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------
# pylint: disable=duplicate-code

from azdev.operations.constant import DISALLOWED_HTML_TAG_RULE_LINK
from ..rule_decorators import CommandGroupRule
from ..linter import RuleError, LinterSeverity
from ..util import has_illegal_html_tag, has_broken_site_links


@CommandGroupRule(LinterSeverity.HIGH)
def missing_group_help(linter, command_group_name):
    if not linter.get_command_group_help(command_group_name) and not linter.command_group_expired(command_group_name) \
            and command_group_name != '':
        raise RuleError('Missing help')


@CommandGroupRule(LinterSeverity.HIGH)
def expired_command_group(linter, command_group_name):
    if linter.command_group_expired(command_group_name):
        raise RuleError("Deprecated command group is expired and should be removed.")


@CommandGroupRule(LinterSeverity.MEDIUM)
def require_wait_command_if_no_wait(linter, command_group_name):
    # If any command within a command group or subgroup exposes the --no-wait parameter,
    # the wait command should be exposed.

    # find commands under this group. A command in this group has one more token than the group name.
    group_command_names = [cmd for cmd in linter.commands if cmd.startswith(command_group_name) and
                           len(cmd.split()) == len(command_group_name.split()) + 1]

    # if one of the commands in this group ends with wait we are good
    for cmd in group_command_names:
        cmds = cmd.split()
        if cmds[-1].lower() == "wait":
            return

    # otherwise there is no wait command. If a command in this group has --no-wait, then error out.
    for cmd in group_command_names:
        if linter.get_command_metadata(cmd).supports_no_wait:
            raise RuleError("Group does not have a 'wait' command, yet '{}' exposes '--no-wait'".format(cmd))


@CommandGroupRule(LinterSeverity.HIGH)
def disallowed_html_tag_from_command_group(linter, command_group_name):
    if command_group_name == '' or not linter.get_loaded_help_entry(command_group_name):
        return
    help_entry = linter.get_loaded_help_entry(command_group_name)
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


@CommandGroupRule(LinterSeverity.MEDIUM)
def broken_site_link_from_command_group(linter, command_group_name):
    if command_group_name == '' or not linter.get_loaded_help_entry(command_group_name):
        return
    help_entry = linter.get_loaded_help_entry(command_group_name)
    if help_entry.short_summary and (broken_links := has_broken_site_links(help_entry.short_summary,
                                                                           linter.diffed_lines)):
        raise RuleError("Broken links {} in short summary. "
                        "If link is an example, please wrap it with backtick. ".format(broken_links))
    if help_entry.long_summary and (broken_links := has_broken_site_links(help_entry.long_summary,
                                                                          linter.diffed_lines)):
        raise RuleError("Broken links {} in long summary. "
                        "If link is an example, please wrap it with backtick. ".format(broken_links))
