# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import time, json, os
from deepdiff import DeepDiff
from .custom import MetaChangeDetects, DiffExportFormat
from azdev.utilities import display, require_azure_cli, heading, get_path_table, filter_by_git_diff
from .util import export_meta_changes_to_json, gen_commands_meta, get_commands_meta
from ..statistics import _create_invoker_and_load_cmds, _get_command_source, _command_codegen_info
from ..statistics.util import filter_modules

from knack.log import get_logger

logger = get_logger(__name__)


def diff_export_format_choices():
    return [form.value for form in DiffExportFormat]


def export_command_meta(modules=None, git_source=None, git_target=None, git_repo=None,
                      with_help=False, with_example=False, meta_output_path=None):
    require_azure_cli()

    # allow user to run only on CLI or extensions
    cli_only = modules == ['CLI']
    ext_only = modules == ['EXT']
    if cli_only or ext_only:
        modules = None

    selected_modules = get_path_table(include_only=modules)

    if cli_only:
        selected_modules['ext'] = {}
    if ext_only:
        selected_modules['mod'] = {}
        selected_modules['core'] = {}

    # filter down to only modules that have changed based on git diff
    selected_modules = filter_by_git_diff(selected_modules, git_source, git_target, git_repo)

    if not any(selected_modules.values()):
        logger.warning('No commands selected to check.')

    selected_mod_names = list(selected_modules['mod'].keys())
    selected_mod_names += list(selected_modules['core'].keys())
    selected_mod_names += list(selected_modules['ext'].keys())

    if selected_mod_names:
        display('Modules: {}\n'.format(', '.join(selected_mod_names)))

    heading('Export Command Table')
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

    commands_info = []

    for command_name, command in command_loader.command_table.items():
        command_info = {
            "name": command_name,
            "source": _get_command_source(command_name, command),
            "is_aaz": False,
            "help": command.help,
            "confirmation": False if command.confirmation is None or command.confirmation is False else True,
            "arguments": [],
            "az_arguments_schema": None,
            "supports_no_wait": command.supports_no_wait,
            "is_preview": command.command_kwargs.get("is_preview", False)
        }
        module_loader = command_loader.cmd_to_loader_map[command_name]
        codegen_info = _command_codegen_info(command_name, command, module_loader)
        if codegen_info:
            command_info['codegen_version'] = codegen_info['version']
            command_info['codegen_type'] = codegen_info['type']
            if codegen_info['version'] == "v2":
                command_info['is_aaz'] = True
        command_loader.load_arguments(command_name)

        if command.arguments is None:
            logger.warning('No arguments generated from {0}.'.format(command_name))
        else:
            command_info['arguments'] = command.arguments
        if command_info["is_aaz"]:
            try:
                command_info['az_arguments_schema'] = command._args_schema
            except Exception as e:
                pass

        commands_info.append(command_info)
    commands_meta = get_commands_meta(command_loader.command_group_table, commands_info, with_help, with_example)
    gen_commands_meta(commands_meta, meta_output_path)
    display(f"Total Commands: {len(commands_info)} for {', '.join(selected_mod_names)} have been generated.")
    return


def cmp_command_meta(base_meta_path, diff_meta_path, only_break=False, output_type="text", output_file=None):
    if not os.path.exists(base_meta_path):
        display("base meta file path needed")
        return
    if not os.path.exists(diff_meta_path):
        display("diff meta file path needed")
        return
    start = time.time()
    with open(base_meta_path, "r") as g:
        command_tree_before = json.load(g)
    with open(diff_meta_path, "r") as g:
        command_tree_after = json.load(g)
    stop = time.time()
    logger.info('Command meta files loaded in %i sec', stop - start)
    diff = DeepDiff(command_tree_before, command_tree_after)
    detected_changes = MetaChangeDetects(diff, command_tree_before, command_tree_after)
    detected_changes.check_deep_diffs()
    result = detected_changes.export_meta_changes(only_break, output_type)
    if output_file:
        export_meta_changes_to_json(result, output_file)
    else:
        return result


