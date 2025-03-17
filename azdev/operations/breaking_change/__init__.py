# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------
import re
import time
from collections import defaultdict
from importlib import import_module

import packaging.version
from knack.log import get_logger

from azdev.operations.statistics import _create_invoker_and_load_cmds  # pylint: disable=protected-access
from azdev.utilities import require_azure_cli, display, heading, output, calc_selected_mod_names
from azdev.utilities.path import calc_selected_modules

# pylint: disable=no-else-return

logger = get_logger(__name__)


class BreakingChangeItem:
    def __init__(self, module, command, detail, target_version):
        self.module = module
        self.command = command
        self.detail = detail
        self.target_version = target_version
        self.group_ref = None

    def calc_ref(self, loader):
        if not loader:
            return
        if self.command in loader.command_group_table:
            self.group_ref = self.command.split()
        else:
            self.group_ref = self.command.split()[:-1]


def _load_commands():
    start = time.time()
    display('Initializing with loading command table...')
    from azure.cli.core import get_default_cli  # pylint: disable=import-error
    az_cli = get_default_cli()

    # load commands, args, and help
    # The arguments must be loaded before the `EVENT_INVOKER_POST_CMD_TBL_CREATE` event.
    # This is because we generate the `deprecate_info` and `upcoming_breaking_change` tags from pre-announcement data
    # during the event.
    # If the arguments are not loaded beforehand, this information will not be included.
    _create_invoker_and_load_cmds(az_cli, load_arguments=True)

    stop = time.time()
    logger.info('Commands loaded in %i sec', stop - start)
    display('Commands loaded in {} sec'.format(stop - start))
    command_loader = az_cli.invocation.commands_loader

    if not command_loader.command_table:
        logger.warning('No commands selected to check.')
    return command_loader


def _handle_custom_breaking_changes(module, command):
    """
    Collect Custom Pre-Announcement defined in `_breaking_change.py`
    :param module: module name
    :param command: command name
    :return: A generated returns Custom Pre-Announcements defined in `_breaking_change.py`
    """
    from azure.cli.core.breaking_change import upcoming_breaking_changes
    yield from _handle_custom_breaking_change(module, command, upcoming_breaking_changes.get(command))
    yield from _handle_custom_breaking_change(module, command, upcoming_breaking_changes.get(f'az {command}'))
    for key in upcoming_breaking_changes:
        if key.startswith(command + '.') or key.startswith(f'az {command}.'):
            yield from _handle_custom_breaking_change(module, command, upcoming_breaking_changes[key])


def _handle_custom_breaking_change(module, command, breaking_change):
    """
    Handle a BreakingChange item defined in `_breaking_change.py`. We need this method because the item stored could
    be a list or object
    """
    from azure.cli.core.breaking_change import BreakingChange
    if isinstance(breaking_change, str):
        yield BreakingChangeItem(module, command, breaking_change, None)
    elif isinstance(breaking_change, BreakingChange):
        yield BreakingChangeItem(module, command, breaking_change.message, breaking_change.target_version.version())
    elif isinstance(breaking_change, list):
        for bc in breaking_change:
            yield from _handle_custom_breaking_change(module, command, bc)


def _handle_status_tag(module, command, status_tag):
    from knack.deprecation import Deprecated
    from azure.cli.core.breaking_change import MergedStatusTag, UpcomingBreakingChangeTag, TargetVersion

    if isinstance(status_tag, MergedStatusTag):
        for tag in status_tag.tags:
            yield from _handle_status_tag(module, command, tag)
    else:
        detail = status_tag._get_message(status_tag)    # pylint: disable=protected-access
        version = None
        if isinstance(status_tag, Deprecated):
            version = status_tag.expiration
        elif isinstance(status_tag, UpcomingBreakingChangeTag):
            if isinstance(status_tag.target_version, TargetVersion):
                version = status_tag.target_version.version()
            elif isinstance(status_tag.target_version, str):
                version = status_tag.target_version
        if version is None:
            version_match = re.search(r'\d+\.\d+\.\d+', detail)
            if version_match:
                version = version_match.group(0)
        yield BreakingChangeItem(module, command, detail, version)


def _handle_command_deprecation(module, command, deprecate_info):
    yield from _handle_status_tag(module, command, deprecate_info)


def _calc_target_of_arg_deprecation(arg_name, arg_settings):
    from knack.deprecation import Deprecated

    option_str_list = []
    depr = arg_settings.get('deprecate_info')
    for option in arg_settings.get('option_list', []):
        if isinstance(option, str):
            option_str_list.append(option)
        elif isinstance(option, Deprecated):
            option_str_list.append(option.target)
    if option_str_list:
        return '/'.join(option_str_list)
    elif hasattr(depr, 'target'):
        return depr.target
    else:
        return arg_name


def _handle_arg_deprecation(module, command, target, deprecation_info):
    deprecation_info.target = target
    yield from _handle_status_tag(module, command, deprecation_info)


def _handle_options_deprecation(module, command, options):
    from knack.deprecation import Deprecated

    deprecate_option_map = defaultdict(lambda: [])
    for option in options:
        if isinstance(option, Deprecated):
            key = f'{option.redirect}|{option.expiration}|{option.hide}'
            deprecate_option_map[key].append(option)
    for _, depr_list in deprecate_option_map.items():
        target = '/'.join([depr.target for depr in depr_list])
        depr = depr_list[0]
        depr.target = target
        yield from _handle_status_tag(module, command, depr)


def _handle_command_breaking_changes(module, command, command_info, source):
    if source == "deprecate_info":
        if hasattr(command_info, "deprecate_info") and command_info.deprecate_info:
            yield from _handle_command_deprecation(module, command, command_info.deprecate_info)

        for argument_name, argument in command_info.arguments.items():
            arg_settings = argument.type.settings
            depr = arg_settings.get('deprecate_info')
            if depr:
                bc_target = _calc_target_of_arg_deprecation(argument_name, arg_settings)
                yield from _handle_arg_deprecation(module, command, bc_target, depr)
            yield from _handle_options_deprecation(module, command, arg_settings.get('options_list', []))
    if source == "pre_announce":
        yield from _handle_custom_breaking_changes(module, command)


def _handle_command_group_deprecation(module, command, deprecate_info):
    yield from _handle_status_tag(module, command, deprecate_info)


def _handle_command_group_breaking_changes(module, command_group_name, command_group_info, source):
    if source == "deprecate_info":
        if hasattr(command_group_info, 'group_kwargs') and command_group_info.group_kwargs.get('deprecate_info'):
            yield from _handle_command_group_deprecation(module, command_group_name,
                                                         command_group_info.group_kwargs.get('deprecate_info'))

    if source == "pre_announce":
        yield from _handle_custom_breaking_changes(module, command_group_name)


def _get_mod_ext_name(loader):
    # There could be different name with module name in extension.
    # For example, module name of `application-insights` is azext_applicationinsights
    try:
        module_source = next(iter(loader.command_table.values())).command_source
        if isinstance(module_source, str):
            return module_source
        else:
            return module_source.extension_name
    except StopIteration:
        logger.warning('There is no command in Loader(%s)', loader)
    mod_path = loader.__class__.__module__
    mod_name = mod_path.rsplit('.', maxsplit=1)[-1]
    mod_name = mod_name.replace('azext_', '', 1)
    return mod_name


def _iter_and_prepare_module_loader(command_loader, selected_mod_names):
    for loader in command_loader.loaders:
        module_path = loader.__class__.__module__
        module_name = module_path.rsplit('.', maxsplit=1)[-1]
        if module_name and module_name not in selected_mod_names:
            continue

        _breaking_change_module = f'{module_path}._breaking_change'
        try:
            import_module(_breaking_change_module)
        except ImportError:
            pass
        loader.skip_applicability = True

        yield module_name, loader


def _handle_module(module, loader, source):
    start = time.time()

    for command, command_info in loader.command_table.items():
        yield from _handle_command_breaking_changes(module, command, command_info, source)

    for command_group_name, command_group in loader.command_group_table.items():
        yield from _handle_command_group_breaking_changes(module, command_group_name, command_group, source)

    stop = time.time()
    logger.info('Module %s finished in %i sec', module, stop - start)
    display('Module {} finished loaded in {} sec'.format(module, stop - start))


def _handle_core(source):
    start = time.time()
    if source == "pre_announce":
        core_module = 'azure.cli.core'
        _breaking_change_module = f'{core_module}._breaking_change'
        try:
            import_module(_breaking_change_module)
        except ImportError:
            pass

        yield from _handle_custom_breaking_changes('core', 'core')

    stop = time.time()
    logger.info('Core finished in %i sec', stop - start)
    display('Core finished loaded in {} sec'.format(stop - start))


def _handle_upcoming_breaking_changes(command_loader, selected_mod_names, source):
    if 'core' in selected_mod_names or 'azure-cli-core' in selected_mod_names:
        yield from _handle_core(source)

    for module, loader in _iter_and_prepare_module_loader(command_loader, selected_mod_names):
        for bc_item in _handle_module(module, loader, source):
            bc_item.calc_ref(loader)
            yield bc_item


def _filter_breaking_changes(iterator, max_version=None):
    if not max_version:
        yield from iterator
        return
    try:
        parsed_max_version = packaging.version.parse(max_version)
    except packaging.version.InvalidVersion:
        logger.warning('Invalid target version: %s; '
                       'Will present all upcoming breaking changes as alternative.', max_version)
        yield from iterator
        return
    for item in iterator:
        if item.target_version:
            try:
                target_version = packaging.version.parse(item.target_version)
                if target_version <= parsed_max_version:
                    yield item
            except packaging.version.InvalidVersion:
                logger.warning('Invalid version from `%s`: %s', item.command, item.target_version)


# pylint: disable=unnecessary-lambda-assignment
def _group_breaking_change_items(iterator, group_by_version=False):
    if group_by_version:
        upcoming_breaking_changes = defaultdict(  # module to command
            lambda: defaultdict(  # command to version
                lambda: {'group_ref': None, 'items': defaultdict(  # version to list of breaking changes
                    lambda: [])}))
    else:
        upcoming_breaking_changes = defaultdict(  # module to command
            lambda: defaultdict(  # command to list of breaking changes
                lambda: {'group_ref': None, 'items': []}))
    for item in iterator:
        version = item.target_version if item.target_version else 'Unspecific'
        upcoming_breaking_changes[item.module][item.command]['group_ref'] = item.group_ref
        if group_by_version:
            upcoming_breaking_changes[item.module][item.command]['items'][version].append(item.detail)
        else:
            upcoming_breaking_changes[item.module][item.command]['items'].append(item.detail)
    return upcoming_breaking_changes


def collect_upcoming_breaking_changes(modules=None, target_version='NextWindow', source=None, group_by_version=None,
                                      output_format='structure', no_head=False, no_tail=False):
    if target_version == 'NextWindow':
        from azure.cli.core.breaking_change import NEXT_BREAKING_CHANGE_RELEASE
        target_version = NEXT_BREAKING_CHANGE_RELEASE
    elif target_version.lower() == 'none':
        target_version = None

    require_azure_cli()

    selected_modules = calc_selected_modules(modules)
    cli_mod_names = list(selected_modules['core'].keys()) + list(selected_modules['mod'].keys())
    ext_mod_names = list(selected_modules['ext'].keys())

    if cli_mod_names or ext_mod_names:
        display('Modules selected: {}\n'.format(', '.join(cli_mod_names + ext_mod_names)))

    command_loader = _load_commands()

    heading('Collecting Breaking Change Pre-announcement')
    breaking_changes = []
    if cli_mod_names:
        cli_breaking_changes = _handle_upcoming_breaking_changes(command_loader, cli_mod_names, source)
        cli_breaking_changes = _filter_breaking_changes(cli_breaking_changes, target_version)
        breaking_changes.extend(cli_breaking_changes)
    if ext_mod_names:
        ext_breaking_changes = _handle_upcoming_breaking_changes(command_loader, ext_mod_names, 'pre_announce')
        breaking_changes.extend(ext_breaking_changes)
    breaking_changes = _group_breaking_change_items(breaking_changes, group_by_version)
    if output_format == 'structure':
        return breaking_changes
    elif output_format == 'markdown':
        from jinja2 import Environment, PackageLoader
        env = Environment(loader=PackageLoader('azdev', 'operations/breaking_change'),
                          trim_blocks=True)
        template = env.get_template('markdown_template.jinja2')
        output(template.render({
            'module_bc': breaking_changes,
            'no_head': no_head,
            'no_tail': no_tail,
        }))
    return None
