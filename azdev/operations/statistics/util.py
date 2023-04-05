# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import copy, json
from knack.log import get_logger

from azdev.utilities import get_name_index


logger = get_logger(__name__)


def filter_modules(command_loader, modules=None, exclude=False, include_whl_extensions=False):
    modules = modules or []

    # command tables and help entries must be copied to allow for seperate linter scope
    command_table = command_loader.command_table.copy()
    command_group_table = command_loader.command_group_table.copy()
    command_loader = copy.copy(command_loader)
    command_loader.command_table = command_table
    command_loader.command_group_table = command_group_table
    name_index = get_name_index(include_whl_extensions=include_whl_extensions)

    for command_name in list(command_loader.command_table.keys()):
        try:
            source_name, _ = _get_command_source(command_name, command_loader.command_table)
        except ValueError as ex:
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

    # Remove unneeded command groups
    retained_command_groups = {' '.join(x.split(' ')[:-1]) for x in command_loader.command_table}
    excluded_command_groups = set(command_loader.command_group_table.keys()) - retained_command_groups

    for group_name in excluded_command_groups:
        command_loader.command_group_table.pop(group_name, None)

    return command_loader


def _get_command_source(command_name, command_table):
    from azure.cli.core.commands import ExtensionCommandSource  # pylint: disable=import-error
    command = command_table.get(command_name)
    # see if command is from an extension
    if isinstance(command.command_source, ExtensionCommandSource):
        return command.command_source.extension_name, True
    if command.command_source is None:
        raise ValueError('Command: `%s`, has no command source.' % command_name)
    # command is from module
    return command.command_source, False


def get_command_tree(command_name):
    name_arr = command_name.split()
    ret = {}
    name_arr.reverse()
    for i, name in enumerate(name_arr):
        tmp = {}
        if i == 0:
            tmp = {
                "is_group": False,
                "cmd_name": " ".join(name_arr[::-1])
            }
        else:
            tmp = {
                "is_group": True,
                "group_name": " ".join(name_arr[len(name_arr):i-1:-1]),
                "sub_info": ret
            }
        ret = tmp
    return ret


def gen_command_meta(command_info):
    command_meta = {
        "name": command_info["name"],
        "desc": command_info["name"],
        "is_aaz": command_info["is_aaz"],
        "confirmation": command_info["confirmation"],
        "parameters": [],
    }
    try:
        command_meta["examples"] = command_info["help"]["examples"]
    except Exception as e:
        pass
    try:
        command_meta["desc"] = command_info["help"]["short-summary"]
    except Exception as e:
        pass
    parameters = []
    for key, argument in command_info["arguments"].items():
        if argument.type is None:
            continue
        settings = argument.type.settings
        para = {
            "name": settings["dest"],
            "options": settings["options_list"],
            "required": settings.get("required", False),
            "desc": settings["help"],
        }
        parameters.append(para)
    command_meta["parameters"] = parameters
    return command_meta


def iter_command_group(commands_meta_iter):
    for key, module_info in commands_meta_iter.items():
        module_info["commands_name"] = list(module_info["commands_name"])
        # module_info["commands"] = module_info["commands"].values()
        module_info["sub_group_name"] = list(module_info["sub_group_name"])
        if len(module_info["sub_group_name"]) > 0:
            iter_command_group(module_info["sub_groups"])
        # module_info["sub_groups"] = module_info["sub_groups"].values()


def get_commands_meta(command_group_table, commands_info):
    commands_meta = {}

    for command_info in commands_info:
        moduel_name = command_info["source"]["module"]
        command_name = command_info["name"]
        if moduel_name not in commands_meta:
            commands_meta[moduel_name] = {
                "module_name": moduel_name,
                "name": "az",
                "desc": "azure cli",
                "commands": {},
                "commands_name": set(),
                "sub_group_name": set(),
                "sub_groups": {}
            }
        command_group_info = commands_meta[moduel_name]
        command_tree = get_command_tree(command_name)
        while True:
            if "is_group" not in command_tree:
                break
            if command_tree["is_group"]:
                group_name = command_tree["group_name"]
                command_group_info["sub_group_name"].add(group_name)
                if group_name not in command_group_info["sub_groups"]:
                    # group_info = command_group_table.get(group_name, None)
                    command_group_info["sub_groups"][group_name] = {
                        "name": group_name,
                        "desc": "az " + group_name,
                        # "desc": group_info.help["short-summary"] if group_info is not None else "az " + group_name,
                        "commands": {},
                        "commands_name": set(),
                        "sub_group_name": set(),
                        "sub_groups": {}
                    }
                command_tree = command_tree["sub_info"]
                command_group_info = command_group_info["sub_groups"][group_name]
            else:
                command_group_info["commands_name"].add(command_name)
                if command_name in command_group_info["commands"]:
                    logger.warning("repeated command: {0}".format(command_name))
                    break
                command_meta = gen_command_meta(command_info)
                command_group_info["commands"][command_name] = command_meta
                break
    iter_command_group(commands_meta)
    return commands_meta


def gen_commands_meta(commands_meta):
    for key, module_info in commands_meta.items():
        file_name = "az_" + key + "_meta.json"
        with open(file_name, "w") as f_out:
            f_out.write(json.dumps(module_info, indent=4))