# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import copy, json
from knack.log import get_logger
import jsbeautifier
from azure.cli.core.aaz import has_value
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
    """
    input: monitor log-profiles create
    ret:
    {
        is_group: True,
        group_name: 'monitor',
        sub_info: {
            is_group: True,
            group_name: 'monitor log-profiles',
            sub_info: {
                is_group: False,
                cmd_name: 'monitor log-profiles create'
            }
        }
    }
    """
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


def process_aaz_argument(az_arguments_schema, argument_settings, para):
    _fields = az_arguments_schema._fields
    aaz_type = _fields.get(argument_settings["dest"], None)
    if aaz_type:
        para["aaz_type"] = aaz_type.__class__.__name__
        para["type"] = aaz_type._type_in_help
        if has_value(aaz_type._default):
            para["aaz_default"] = aaz_type._default
        if para["aaz_type"] in ["AAZArgEnum"] and aaz_type.get("enum", None) and aaz_type.enum.get("items", None):
            para["aaz_choices"] = aaz_type.enum["items"]


def gen_command_meta(command_info, with_help=False, with_example=False):
    stored_property_when_exist = ["confirmation", "supports_no_wait", "is_preview"]
    command_meta = {
        "name": command_info["name"],
        "is_aaz": command_info["is_aaz"],
    }
    for property in stored_property_when_exist:
        if command_info[property]:
            command_meta[property] = command_info[property]
    if with_example:
        try:
            command_meta["examples"] = command_info["help"]["examples"]
        except Exception as e:
            pass
    if with_help:
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
            "options": sorted(settings["options_list"])
        }
        if settings.get("required", False):
            para["required"] = True
        if settings.get("choices", None):
            para["choices"] = sorted(list(settings["choices"]))
        if settings.get("id_part", None):
            para["id_part"] = settings["id_part"]
        if settings.get("nargs", None):
            para["nargs"] = settings["nargs"]
        if settings.get("default", None):
            para["default"] = settings["default"]
        if with_help:
            para["desc"] = settings["help"]
        if command_info["is_aaz"] and command_info["az_arguments_schema"]:
            process_aaz_argument(command_info["az_arguments_schema"], settings, para)
        parameters.append(para)
    command_meta["parameters"] = parameters
    return command_meta


def adjust_command_group(commands_meta_iter):
    for key, module_info in commands_meta_iter.items():
        pass
        # module_info["command_name"] = sorted(module_info["command_name"])
        # module_info["commands"] = module_info["commands"].values()
        # module_info["sub_group_name"] = sorted(module_info["sub_group_name"])
        # if len(module_info["sub_group_name"]) > 0:
        #     adjust_command_group(module_info["sub_groups"])
        # module_info["sub_groups"] = module_info["sub_groups"].values()


def get_commands_meta(command_group_table, commands_info, with_help, with_example):
    commands_meta = {}

    for command_info in commands_info[131:]:
        moduel_name = command_info["source"]["module"]
        command_name = command_info["name"]
        if moduel_name not in commands_meta:
            commands_meta[moduel_name] = {
                "module_name": moduel_name,
                "name": "az",
                # "command_name": set(),
                # "sub_group_name": set(),
                "commands": {},
                "sub_groups": {}
            }
        command_group_info = commands_meta[moduel_name]
        command_tree = get_command_tree(command_name)
        while True:
            if "is_group" not in command_tree:
                break
            if command_tree["is_group"]:
                group_name = command_tree["group_name"]
                # command_group_info["sub_group_name"].add(group_name)
                if group_name not in command_group_info["sub_groups"]:
                    group_info = command_group_table.get(group_name, None)
                    command_group_info["sub_groups"][group_name] = {
                        "name": group_name,
                        # "command_name": set(),
                        # "sub_group_name": set(),
                        "commands": {},
                        "sub_groups": {}
                    }
                    if with_help:
                        try:
                            command_group_info["sub_groups"][group_name]["desc"] = group_info.help["short-summary"]
                        except Exception as e:
                            pass

                command_tree = command_tree["sub_info"]
                command_group_info = command_group_info["sub_groups"][group_name]
            else:
                # command_group_info["command_name"].add(command_name)
                if command_name in command_group_info["commands"]:
                    logger.warning("repeated command: {0}".format(command_name))
                    break
                command_meta = gen_command_meta(command_info, with_help, with_example)
                command_group_info["commands"][command_name] = command_meta
                break
    adjust_command_group(commands_meta)
    return commands_meta


def gen_commands_meta(commands_meta):
    options = jsbeautifier.default_options()
    options.indent_size = 4
    for key, module_info in commands_meta.items():
        file_name = "az_" + key + "_meta.json"
        with open(file_name, "w") as f_out:
            f_out.write(jsbeautifier.beautify(json.dumps(module_info), options))