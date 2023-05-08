# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------
import ast
import inspect
import json
import os
import re
import textwrap
import time
from importlib import import_module
from pathlib import Path

from knack.log import get_logger
from azdev.utilities import (
    heading, display, get_path_table, require_azure_cli, filter_by_git_diff)

from .util import filter_modules

logger = get_logger(__name__)


def list_command_table(modules=None, git_source=None, git_target=None, git_repo=None,
                       include_whl_extensions=False, statistics_only=False):
    require_azure_cli()

    from azure.cli.core import get_default_cli  # pylint: disable=import-error

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

    selected_mod_names = list(selected_modules['mod'].keys())
    selected_mod_names += list(selected_modules['core'].keys())
    selected_mod_names += list(selected_modules['ext'].keys())
    # selected_mod_paths = list(selected_modules['mod'].values()) + list(selected_modules['core'].values()) + \
    #                      list(selected_modules['ext'].values())

    if selected_mod_names:
        display('Modules: {}\n'.format(', '.join(selected_mod_names)))

    start = time.time()
    display('Initializing with command table and help files...')
    az_cli = get_default_cli()

    # load commands, args, and help
    _create_invoker_and_load_cmds(az_cli)

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
        command_info = {
            "name": command_name,
            "source": _get_command_source(command_name, command)
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

    if statistics_only:
        return {
            "total": len(commands),
            "codegenV2": codegen_v2_command_count,
            "codegenV1": codegen_v1_command_count,
        }

    display(f"Total Commands: {len(commands)}\t "
            f"CodeGen V2 Commands: {codegen_v2_command_count}\t "
            f"CodeGen V1 Commands: {codegen_v1_command_count}")

    commands = sorted(commands, key=lambda a: a['name'])
    return commands


def diff_command_tables(table_path, diff_table_path, statistics_only=False):
    with open(table_path, 'r') as f:
        commands = json.load(f)

    with open(diff_table_path, 'r') as f:
        new_commands = json.load(f)

    command_table = {}
    for command in commands:
        command_table[command['name']] = command

    added_commands = []
    migrated_commands = []
    for command in new_commands:
        name = command['name']
        if name not in command_table:
            added_commands.append(command)
        elif command != command_table[name] and command.get('codegen_version', None) != command_table[name].get(
                'codegen_version', None):
            migrated_commands.append(command)

    added_v1_commands_count = 0
    added_v2_commands_count = 0
    for command in added_commands:
        if command.get('codegen_version', None) == "v2":
            added_v2_commands_count += 1
        elif command.get('codegen_version', None) == "v1":
            added_v1_commands_count += 1

    migrated_v1_commands_count = 0
    migrated_v2_commands_count = 0
    for command in migrated_commands:
        if command.get('codegen_version', None) == "v2":
            migrated_v2_commands_count += 1
        elif command.get('codegen_version', None) == "v1":
            migrated_v1_commands_count += 1

    if statistics_only:
        return {
            "newCommands": {
                "total": len(added_commands),
                "codegenV2": added_v2_commands_count,
                "codegenv1": added_v1_commands_count,
            },
            "migratedCommands": {
                "total": len(migrated_commands),
                "codegenV2": migrated_v2_commands_count,
                "codegenv1": migrated_v1_commands_count,
            }
        }

    display(f"Total New Commands: {len(added_commands)}\t "
            f"CodeGen V2 Commands: {added_v2_commands_count}\t "
            f"CodeGen V1 Commands: {added_v1_commands_count}")

    display(f"Total Migrated Commands: {len(migrated_commands)}\t "
            f"CodeGen V2 Commands: {migrated_v2_commands_count}\t "
            f"CodeGen V1 Commands: {migrated_v1_commands_count}")

    return {
        "newCommands": added_commands,
        "migratedCommands": migrated_commands,
    }


def _get_command_source(command_name, command):
    from azure.cli.core.commands import ExtensionCommandSource  # pylint: disable=import-error
    if isinstance(command.command_source, ExtensionCommandSource):
        return {
            "module": command.command_source.extension_name,
            "isExtension": True
        }
    if command.command_source is None:
        raise ValueError('Command: `%s`, has no command source.' % command_name)
    # command is from module
    return {
        "module": command.command_source,
        "isExtension": False
    }


def _create_invoker_and_load_cmds(cli_ctx):
    from knack.events import (
        EVENT_INVOKER_PRE_CMD_TBL_CREATE, EVENT_INVOKER_POST_CMD_TBL_CREATE)
    from azure.cli.core.commands import register_cache_arguments
    from azure.cli.core.commands.arm import register_global_subscription_argument, register_ids_argument

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


def _command_codegen_info(command_name, command, module_loader):  # pylint: disable=unused-argument, too-many-branches, too-many-statements
    from azure.cli.core.commands import AzCliCommand

    try:
        from azure.cli.core.aaz import AAZCommand
        if isinstance(command, AAZCommand):
            return {
                "version": "v2",
                "type": "Atomic"
            }
    except ImportError:
        pass

    if isinstance(command, AzCliCommand):
        if 'command_operation' not in command.command_kwargs:
            return None

        command_operation = command.command_kwargs['command_operation']
        is_v2_convenience = False
        is_generated = False
        if getattr(command_operation, 'op_path', None):
            operation_path = command_operation.op_path
            operation_module_path = operation_path.split("#")[0]
            op = command_operation.get_op_handler(operation_path)
            func_map = _get_module_functions(operation_module_path)
            op_source = _expand_all_functions(op, func_map)
            for line in op_source.splitlines():
                if import_aaz_express.match(line):
                    is_v2_convenience = True
                    break
                if command_args_express.match(line):
                    is_v2_convenience = True

            path_parts = list(Path(inspect.getfile(op)).parts)
            if "generated" in path_parts:
                is_generated = True

        if not is_v2_convenience and getattr(command_operation, 'getter_op_path', None):
            op = command_operation.get_op_handler(command_operation.getter_op_path)
            op_source = inspect.getsource(op)
            for line in op_source.splitlines():
                if import_aaz_express.match(line):
                    is_v2_convenience = True
                    break
                if command_args_express.match(line):
                    is_v2_convenience = True

            path_parts = list(Path(inspect.getfile(op)).parts)
            if "generated" in path_parts:
                is_generated = True

        if not is_v2_convenience and getattr(command_operation, 'setter_op_path', None):
            op = command_operation.get_op_handler(command_operation.setter_op_path)
            op_source = inspect.getsource(op)
            for line in op_source.splitlines():
                if import_aaz_express.match(line):
                    is_v2_convenience = True
                    break
                if command_args_express.match(line):
                    is_v2_convenience = True

            path_parts = list(Path(inspect.getfile(op)).parts)
            if "generated" in path_parts:
                is_generated = True

        if not is_v2_convenience and getattr(command_operation, 'custom_function_op_path', None):
            op = command_operation.get_op_handler(command_operation.custom_function_op_path)
            op_source = inspect.getsource(op)
            for line in op_source.splitlines():
                if import_aaz_express.match(line):
                    is_v2_convenience = True
                    break
                if command_args_express.match(line):
                    is_v2_convenience = True

            path_parts = list(Path(inspect.getfile(op)).parts)
            if "generated" in path_parts:
                is_generated = True

        if is_v2_convenience:
            return {
                "version": "v2",
                "type": "Convenience"
            }

        if is_generated:
            return {
                "version": "v1",
                "type": "SDK"
            }

    return None


def _get_module_functions(path):
    try:
        module = import_module(path)
        functions = inspect.getmembers(module, predicate=inspect.isfunction)
        return dict(functions)

    except ModuleNotFoundError:
        return None  # bypass functions in sdk


def _expand_all_functions(func, func_map):
    source = textwrap.dedent(inspect.getsource(func))
    if func_map is None:
        return source

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            function_name = node.func.id
            function = func_map.get(function_name, None)
            # skip recursion and `locals()`
            if function_name == func.__name__ or function is None:
                continue

            source += _expand_all_functions(function, func_map)

    return source
