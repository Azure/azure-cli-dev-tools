# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

# pylint: disable=no-else-return, too-many-nested-blocks, too-many-locals, too-many-branches

import time

from knack.log import get_logger
import azure_cli_diff_tool
from azdev.utilities import display, require_azure_cli, heading, get_path_table, filter_by_git_diff, \
    calc_selected_mod_names
from .custom import DiffExportFormat, get_commands_meta, STORED_DEPRECATION_KEY
from .util import export_commands_meta, dump_command_tree, add_to_command_tree
from ..statistics import _create_invoker_and_load_cmds, _get_command_source, \
    _command_codegen_info  # pylint: disable=protected-access
from ..statistics.util import filter_modules


logger = get_logger(__name__)


def diff_export_format_choices():
    return [form.value for form in DiffExportFormat]


# pylint: disable=too-many-statements
def export_command_meta(modules=None, git_source=None, git_target=None, git_repo=None,
                        with_help=False, with_example=False, include_whl_extensions=False,
                        meta_output_path=None):
    require_azure_cli()

    # allow user to run only on CLI or extensions
    cli_only = modules == ['CLI']
    ext_only = modules == ['EXT']
    if cli_only or ext_only:
        modules = None

    selected_modules = get_path_table(include_only=modules, include_whl_extensions=include_whl_extensions)

    if cli_only:
        selected_modules['ext'] = {}
    if ext_only:
        selected_modules['core'] = {}
        selected_modules['mod'] = {}

    # filter down to only modules that have changed based on git diff
    selected_modules = filter_by_git_diff(selected_modules, git_source, git_target, git_repo)

    if not any(selected_modules.values()):
        logger.warning('No commands selected to check.')

    selected_mod_names = list(selected_modules['mod'].keys())
    selected_mod_names += list(selected_modules['ext'].keys())
    selected_mod_names += list(selected_modules['core'].keys())

    if selected_mod_names:
        display('Modules selected: {}\n'.format(', '.join(selected_mod_names)))

    heading('Export Command Table Meta')
    start = time.time()
    display('Initializing with loading command table...')
    from azure.cli.core import get_default_cli  # pylint: disable=import-error
    az_cli = get_default_cli()

    # load commands, args, and help
    _create_invoker_and_load_cmds(az_cli)

    stop = time.time()
    logger.info('Commands loaded in %i sec', stop - start)
    display('Commands loaded in {} sec'.format(stop - start))
    command_loader = az_cli.invocation.commands_loader

    from azure.cli.core.file_util import get_all_help

    help_info = {}
    if with_help or with_example:
        help_files = get_all_help(az_cli)
        for help_item in help_files:
            if not help_item.command:
                continue
            help_info[help_item.command] = help_item

    # trim command table to selected_modules
    command_loader = filter_modules(command_loader, modules=selected_mod_names,
                                    include_whl_extensions=include_whl_extensions)

    if not command_loader.command_table:
        logger.warning('No commands selected to check.')

    commands_info = []

    for command_name, command in command_loader.command_table.items():
        command_info = {
            "name": command_name,
            "source": _get_command_source(command_name, command),
            "is_aaz": False,
            "help": help_info[command_name] if command_name in help_info else None,
            "confirmation": command.confirmation is True,
            "arguments": [],
            "az_arguments_schema": None,
            "supports_no_wait": command.supports_no_wait,
            "is_preview": command.command_kwargs.get("is_preview", False)
        }

        if hasattr(command, "deprecate_info"):
            for info_key in STORED_DEPRECATION_KEY:
                if hasattr(command.deprecate_info, info_key) and getattr(command.deprecate_info, info_key):
                    if command_info.get("deprecate_info", None) is None:
                        command_info["deprecate_info"] = {}
                    command_info["deprecate_info"][info_key] = getattr(command.deprecate_info, info_key)

        module_loader = command_loader.cmd_to_loader_map[command_name]
        for loader in module_loader:
            loader.skip_applicability = True
        codegen_info = _command_codegen_info(command_name, command, module_loader)
        if codegen_info:
            command_info['codegen_version'] = codegen_info['version']
            command_info['codegen_type'] = codegen_info['type']
            if codegen_info['version'] == "v2":
                command_info['is_aaz'] = True
        command_loader.load_arguments(command_name)

        if command.arguments is None:
            logger.warning('No arguments generated from %i.', command_name)
        else:
            command_info['arguments'] = command.arguments
        if command_info["is_aaz"]:
            try:
                command_info['az_arguments_schema'] = command._args_schema  # pylint: disable=protected-access
            except AttributeError:
                pass

        commands_info.append(command_info)
    commands_meta = get_commands_meta(command_loader.command_group_table, commands_info, with_help, with_example)
    export_commands_meta(commands_meta, meta_output_path)
    display(f"Total Commands: {len(commands_info)} from {', '.join(selected_mod_names)} have been generated.")


def cmp_command_meta(base_meta_file, diff_meta_file, only_break=False, output_type="text", output_file=None):
    return azure_cli_diff_tool.meta_diff(base_meta_file, diff_meta_file, only_break, output_type, output_file)


def export_command_tree(modules, output_file=None):
    require_azure_cli()

    selected_mod_names = calc_selected_mod_names(modules)

    if selected_mod_names:
        display('Modules selected: {}\n'.format(', '.join(selected_mod_names)))

    heading('Export Command Tree')
    start = time.time()
    display('Initializing with loading command table...')
    from azure.cli.core import get_default_cli  # pylint: disable=import-error
    az_cli = get_default_cli()

    # load commands, args, and help
    _create_invoker_and_load_cmds(az_cli)

    stop = time.time()
    logger.info('Commands loaded in %i sec', stop - start)
    display('Commands loaded in {} sec'.format(stop - start))
    command_loader = az_cli.invocation.commands_loader

    # trim command table to selected_modules
    command_loader = filter_modules(command_loader, modules=selected_mod_names)

    if not command_loader.command_table:
        logger.warning('No commands selected to check.')

    command_tree = {}

    for command_name, command in command_loader.command_table.items():
        module_source = _get_command_source(command_name, command)['module']
        # The command tree is a tree structure like our azExtCmdTree: https://aka.ms/azExtCmdTree
        add_to_command_tree(command_tree, command_name, module_source)

    dump_command_tree(command_tree, output_file)
