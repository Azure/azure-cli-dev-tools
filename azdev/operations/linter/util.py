# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import copy
import re
import requests

from knack.log import get_logger

from azdev.utilities import get_name_index
from azdev.operations.constant import ALLOWED_HTML_TAG


logger = get_logger(__name__)


_LOADER_CLS_RE = re.compile('.*azure/cli/command_modules/(?P<module>[^/]*)/__init__.*')

# add html tag extraction for <abd>, <lun1>, <edge zone>
# html tag search for <os_des>, <lun1_des> is enabled in cli ci but skipped in doc build cause internal issue
_HTML_TAG_RE = re.compile(r'<([^\n>]+)>')

_HTTP_LINK_RE = re.compile(r'(?<!`)(https?://[^\s`]+)(?!`)')


def filter_modules(command_loader, help_file_entries, modules=None, include_whl_extensions=False):
    """ Modify the command table and help entries to only include certain modules/extensions.

    : param command_loader: The CLICommandsLoader containing the command table to filter.
    : help_file_entries: The dict of HelpFile entries to filter.
    : modules: [str] list of module or extension names to retain.
    """
    return _filter_mods(command_loader, help_file_entries, modules=modules,
                        include_whl_extensions=include_whl_extensions)


def exclude_commands(command_loader, help_file_entries, module_exclusions, include_whl_extensions=False):
    """ Modify the command table and help entries to exclude certain modules/extensions.

    : param command_loader: The CLICommandsLoader containing the command table to filter.
    : help_file_entries: The dict of HelpFile entries to filter.
    : modules: [str] list of module or extension names to remove.
    """
    return _filter_mods(command_loader, help_file_entries, modules=module_exclusions, exclude=True,
                        include_whl_extensions=include_whl_extensions)


def _filter_mods(command_loader, help_file_entries, modules=None, exclude=False, include_whl_extensions=False):
    modules = modules or []

    # command tables and help entries must be copied to allow for seperate linter scope
    command_table = command_loader.command_table.copy()
    command_group_table = command_loader.command_group_table.copy()
    command_loader = copy.copy(command_loader)
    command_loader.command_table = command_table
    command_loader.command_group_table = command_group_table
    help_file_entries = help_file_entries.copy()
    name_index = get_name_index(include_whl_extensions=include_whl_extensions)

    for command_name in list(command_loader.command_table.keys()):
        try:
            source_name, _ = _get_command_source(command_name, command_loader.command_table)
        except LinterError as ex:
            # command is unrecognized
            logger.warning(ex)
            source_name = None

        try:
            long_name = name_index[source_name]
            is_specified = source_name in modules or long_name in modules
        except KeyError:
            is_specified = False
        if is_specified == exclude:
            # brute force method of ignoring commands from a module or extension
            command_loader.command_table.pop(command_name, None)
            help_file_entries.pop(command_name, None)

    # Remove unneeded command groups
    retained_command_groups = {' '.join(x.split(' ')[:-1]) for x in command_loader.command_table}
    excluded_command_groups = set(command_loader.command_group_table.keys()) - retained_command_groups

    for group_name in excluded_command_groups:
        command_loader.command_group_table.pop(group_name, None)
        help_file_entries.pop(group_name, None)

    return command_loader, help_file_entries


def share_element(first_iter, second_iter):
    return any(element in first_iter for element in second_iter)


def _get_command_source(command_name, command_table):
    from azure.cli.core.commands import ExtensionCommandSource  # pylint: disable=import-error
    command = command_table.get(command_name)
    # see if command is from an extension
    if isinstance(command.command_source, ExtensionCommandSource):
        return command.command_source.extension_name, True
    if command.command_source is None:
        raise LinterError('Command: `%s`, has no command source.' % command_name)
    # command is from module
    return command.command_source, False


# pylint: disable=line-too-long
def merge_exclusion(left_exclusion, right_exclusion):
    for command_name, value in right_exclusion.items():
        for rule_name in value.get('rule_exclusions', []):
            left_exclusion.setdefault(command_name, {}).setdefault('rule_exclusions', []).append(rule_name)
        for param_name in value.get('parameters', {}):
            for rule_name in value.get('parameters', {}).get(param_name, {}).get('rule_exclusions', []):
                left_exclusion.setdefault(command_name, {}).setdefault('parameters', {}).setdefault(param_name, {}).setdefault('rule_exclusions', []).append(rule_name)


class LinterError(Exception):
    """
    Exception thrown by linter for non rule violation reasons
    """
    pass  # pylint: disable=unnecessary-pass


# pylint: disable=line-too-long
def has_illegal_html_tag(help_message, filtered_lines=None):
    """
    Detect those content wrapped with <> but illegal html tag.
    Refer to rule doc: https://review.learn.microsoft.com/en-us/help/platform/validation-ref/disallowed-html-tag?branch=main
    """
    html_matches = re.findall(_HTML_TAG_RE, help_message)
    unbackticked_matches = [match for match in html_matches if not re.search(r'`[^`]*' + re.escape('<' + match + '>') + r'[^`]*`', help_message)]
    disallowed_html_tags = set(unbackticked_matches) - set(ALLOWED_HTML_TAG)
    if filtered_lines:
        disallowed_html_tags = [s for s in disallowed_html_tags if any(('<' + s + '>') in diff_line for diff_line in filtered_lines)]
    return ['<' + s + '>' for s in disallowed_html_tags]


def has_broken_site_links(help_message, filtered_lines=None):
    """
    Detect broken link in help message.
    Refer to rule doc: https://review.learn.microsoft.com/en-us/help/platform/validation-ref/other-site-link-broken?branch=main
    """
    urls = re.findall(_HTTP_LINK_RE, help_message)
    invalid_urls = []

    for url in urls:
        url = re.sub(r'[.")\'\s]*$', '', url)
        try:
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                invalid_urls.append(url)
        except requests.exceptions.RequestException:
            invalid_urls.append(url)
    if filtered_lines:
        invalid_urls = [s for s in invalid_urls if any(s in diff_line for diff_line in filtered_lines)]
    return invalid_urls
