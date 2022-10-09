# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------
import inspect
import re
import time
import os
from pathlib import Path

from azdev.utilities import (
    heading, display, get_path_table, require_azure_cli, filter_by_git_diff)
from knack.log import get_logger

# from .linter import LinterManager, LinterScope, RuleError, LinterSeverity
from .util import filter_modules

logger = get_logger(__name__)

def list_command_table(modules=None, git_source=None, git_target=None, git_repo=None, include_whl_extensions=False, statistics_only=False):
    require_azure_cli()

    from azure.cli.core import get_default_cli  # pylint: disable=import-error
    # from azure.cli.core.file_util import create_invoker_and_load_cmds_and_args  # pylint: disable=import-error

    heading('List Command Table')

    # allow user to run only on CLI or extensions
    cli_only = modules == ['CLI']
    ext_only = modules == ['EXT']
    if cli_only or ext_only:
        modules = None

    selected_modules = get_path_table(include_only=modules, include_whl_extensions=include_whl_extensions)

    if cli_only:
        selected_modules['ext'] = {}
    if ext_only:
        selected_modules['mod'] = {}
        selected_modules['core'] = {}

    # filter down to only modules that have changed based on git diff
    selected_modules = filter_by_git_diff(selected_modules, git_source, git_target, git_repo)

    if not any(selected_modules.values()):
        logger.warning('No commands selected to check.')

    selected_mod_names = list(selected_modules['mod'].keys()) + list(selected_modules['core'].keys()) + \
                         list(selected_modules['ext'].keys())
    selected_mod_paths = list(selected_modules['mod'].values()) + list(selected_modules['core'].values()) + \
                         list(selected_modules['ext'].values())

    if selected_mod_names:
        display('Modules: {}\n'.format(', '.join(selected_mod_names)))

    start = time.time()
    display('Initializing with command table and help files...')
    az_cli = get_default_cli()

    # load commands, args, and help
    create_invoker_and_load_cmds(az_cli)

    stop = time.time()
    logger.info('Commands and help loaded in %i sec', stop - start)
    command_loader = az_cli.invocation.commands_loader

    # trim command table and help to just selected_modules
    command_loader = filter_modules(
        command_loader, modules=selected_mod_names, include_whl_extensions=include_whl_extensions)

    if not command_loader.command_table:
        logger.warning('No commands selected to check.')

    commands = []

    codegen_v2_command_count = 0
    codegen_v1_command_count = 0
    for command_name, command in command_loader.command_table.items():
        # if hasattr(module_loader, '')
        command_info = {
            "name": command_name
        }
        module_loader = command_loader.cmd_to_loader_map[command_name]
        codegen_info = _command_codegen_info(command_name, command, module_loader)
        if codegen_info:
            command_info['codegen_version'] = codegen_info['version']
            command_info['codegen_type'] = codegen_info['type']
            if codegen_info['version'] == "v2":
                codegen_v2_command_count += 1
            if codegen_info['version'] == "v1":
                codegen_v1_command_count += 1

        commands.append(command_info)

    display(f"Total Commands: {len(commands)}\t "
            f"CodeGen V2 Commands: {codegen_v2_command_count}\t "
            f"CodeGen V1 Commands: {codegen_v1_command_count}")

    if statistics_only:
        return

    commands = sorted(commands, key=lambda a: a['name'])
    return commands

def create_invoker_and_load_cmds(cli_ctx):
    from knack.events import (
        EVENT_INVOKER_PRE_CMD_TBL_CREATE, EVENT_INVOKER_POST_CMD_TBL_CREATE)
    from azure.cli.core.commands import register_cache_arguments
    from azure.cli.core.commands.arm import register_global_subscription_argument, register_ids_argument
    from azure.cli.core.commands.events import (
        EVENT_INVOKER_PRE_LOAD_ARGUMENTS, EVENT_INVOKER_POST_LOAD_ARGUMENTS)
    import time

    start_time = time.time()

    register_global_subscription_argument(cli_ctx)
    register_ids_argument(cli_ctx)
    register_cache_arguments(cli_ctx)

    invoker = cli_ctx.invocation_cls(cli_ctx=cli_ctx, commands_loader_cls=cli_ctx.commands_loader_cls,
                                     parser_cls=cli_ctx.parser_cls, help_cls=cli_ctx.help_cls)
    cli_ctx.invocation = invoker
    invoker.commands_loader.skip_applicability = True

    cli_ctx.raise_event(EVENT_INVOKER_PRE_CMD_TBL_CREATE, args=[])
    invoker.commands_loader.load_command_table(None)
    invoker.commands_loader.command_name = ''

    # cli_ctx.raise_event(EVENT_INVOKER_PRE_LOAD_ARGUMENTS, commands_loader=invoker.commands_loader)
    # invoker.commands_loader.load_arguments()
    # cli_ctx.raise_event(EVENT_INVOKER_POST_LOAD_ARGUMENTS, commands_loader=invoker.commands_loader)

    cli_ctx.raise_event(EVENT_INVOKER_POST_CMD_TBL_CREATE, commands_loader=invoker.commands_loader)
    invoker.parser.cli_ctx = cli_ctx
    invoker.parser.load_command_table(invoker.commands_loader)

    end_time = time.time()
    logger.info('Time to load entire command table: %.3f sec', end_time - start_time)


import_aaz_express = re.compile(r'^\s*from (.*\.)?aaz(\..*)? .*$')
command_args_express = re.compile(r'^.*[\s\(]command_args=.*$')


def _command_codegen_info(command_name, command, module_loader):
    from azure.cli.core.aaz import AAZCommand
    from azure.cli.core.commands import AzCliCommand
    if isinstance(command, AAZCommand):
        return {
            "version": "v2",
            "type": "Atomic"
        }

    if isinstance(command, AzCliCommand):
        if 'command_operation' not in command.command_kwargs:
            return

        command_operation = command.command_kwargs['command_operation']
        is_v2_conveniance = False
        is_generated = False
        if getattr(command_operation, 'op_path', None):
            op = command_operation.get_op_handler(command_operation.op_path)
            op_source = inspect.getsource(op)
            for line in op_source.splitlines():
                if import_aaz_express.match(line):
                    is_v2_conveniance = True
                    break
                if command_args_express.match(line):
                    is_v2_conveniance = True

            path_parts = list(Path(inspect.getfile(op)).parts)
            if "generated" in path_parts:
                is_generated = True

        if not is_v2_conveniance and getattr(command_operation, 'getter_op_path', None):
            op = command_operation.get_op_handler(command_operation.getter_op_path)
            op_source = inspect.getsource(op)
            for line in op_source.splitlines():
                if import_aaz_express.match(line):
                    is_v2_conveniance = True
                    break
                if command_args_express.match(line):
                    is_v2_conveniance = True

            path_parts = list(Path(inspect.getfile(op)).parts)
            if "generated" in path_parts:
                is_generated = True

        if not is_v2_conveniance and getattr(command_operation, 'setter_op_path', None):
            op = command_operation.get_op_handler(command_operation.setter_op_path)
            op_source = inspect.getsource(op)
            for line in op_source.splitlines():
                if import_aaz_express.match(line):
                    is_v2_conveniance = True
                    break
                if command_args_express.match(line):
                    is_v2_conveniance = True

            path_parts = list(Path(inspect.getfile(op)).parts)
            if "generated" in path_parts:
                is_generated = True

        if not is_v2_conveniance and getattr(command_operation, 'custom_function_op_path', None):
            op = command_operation.get_op_handler(command_operation.custom_function_op_path)
            op_source = inspect.getsource(op)
            for line in op_source.splitlines():
                if import_aaz_express.match(line):
                    is_v2_conveniance = True
                    break
                if command_args_express.match(line):
                    is_v2_conveniance = True

            path_parts = list(Path(inspect.getfile(op)).parts)
            if "generated" in path_parts:
                is_generated = True

        if is_v2_conveniance:
            return {
                "version": "v2",
                "type": "Convenience"
            }
        elif is_generated:
            return {
                "version": "v1",
                "type": "SDK"
            }
