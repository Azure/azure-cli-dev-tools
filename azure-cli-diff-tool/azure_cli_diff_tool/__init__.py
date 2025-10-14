# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------


# pylint: disable=too-many-lines
# pylint: disable=too-many-statements
import os
import json
import time
from enum import Enum
import logging
from deepdiff import DeepDiff
from .meta_change_detect import MetaChangeDetect
from .utils import get_blob_config, load_blob_config_file, get_target_version_modules, get_target_version_module, \
    extract_module_name_from_meta_file, export_meta_changes_to_csv, export_meta_changes_to_json, \
    export_meta_changes_to_dict, expand_deprecate_obj

__VERSION__ = '0.1.1'

logger = logging.getLogger(__name__)


class DiffExportFormat(Enum):
    DICT = "dict"
    TEXT = "text"
    TREE = "tree"


def diff_export_format_choices():
    return [form.value for form in DiffExportFormat]


def check_meta_tool_compatibility(meta_version):
    if not meta_version:
        return False
    meta_version_vec = meta_version.split(".")
    tool_version_vec = __VERSION__.split(".")
    version_outdated = False
    for ind, v in enumerate(meta_version_vec):
        if v.isdigit() and tool_version_vec[ind].isdigit() and int(v) > int(tool_version_vec[ind]):
            version_outdated = True
    return version_outdated


def meta_diff(base_meta_file, diff_meta_file, only_break=False, output_type="text", output_file=None):
    if not os.path.exists(base_meta_file):
        raise Exception("base meta file needed")
    if not os.path.exists(diff_meta_file):
        raise Exception("diff meta file needed")

    with open(base_meta_file, "r") as g:
        command_tree_before = json.load(g)
    with open(diff_meta_file, "r") as g:
        command_tree_after = json.load(g)
    if command_tree_before.get("compat_version", None) \
            and check_meta_tool_compatibility(command_tree_before["compat_version"]):
        raise Exception("Please update your azure cli diff tool")
    if command_tree_after.get("compat_version", None) \
            and check_meta_tool_compatibility(command_tree_after["compat_version"]):
        raise Exception("Please update your azure cli diff tool")
    expand_deprecate_obj(command_tree_before)
    expand_deprecate_obj(command_tree_after)
    diff = DeepDiff(command_tree_before, command_tree_after, exclude_paths=["root['module_name']"])
    if not diff:
        print(f"No meta diffs from {diff_meta_file} to {base_meta_file}")
        return export_meta_changes_to_json(None, output_file)
    else:
        detected_changes = MetaChangeDetect(diff, command_tree_before, command_tree_after)
        detected_changes.check_deep_diffs()
        result = detected_changes.export_meta_changes(only_break, output_type)
        return export_meta_changes_to_json(result, output_file)


def version_diff(base_version, diff_version, only_break=False, version_diff_file=None, use_cache=False,
                 output_type="dict", target_module=None):
    config = load_blob_config_file()
    blob_url, path_prefix, index_file = get_blob_config(config)
    download_base_start = time.time()
    if target_module:
        base_version_module_list = get_target_version_module(blob_url, path_prefix, base_version,
                                                             target_module, use_cache)
    else:
        base_version_module_list = get_target_version_modules(blob_url, path_prefix, index_file, base_version, use_cache)
    download_base_end = time.time()
    logger.info("base version {} meta files download using {} sec".format(base_version,
                                                                          download_base_end - download_base_start))
    if target_module:
        get_target_version_module(blob_url, path_prefix, diff_version,
                                  target_module, use_cache)
    else:
        get_target_version_modules(blob_url, path_prefix, index_file, diff_version, use_cache)
    download_target_end = time.time()
    logger.info("diff version {} meta files download using {} sec".format(diff_version,
                                                                          download_target_end - download_base_end))
    version_diffs = []
    for _, base_meta_file_full_path, base_meta_file in base_version_module_list:
        module_name = extract_module_name_from_meta_file(base_meta_file)
        if not module_name:
            continue
        if target_module and module_name != target_module:
            continue
        diff_meta_file_full_path = os.path.join(os.getcwd(), path_prefix + diff_version, base_meta_file)
        if not os.path.exists(diff_meta_file_full_path):
            print(f"Module {module_name} removed for {diff_version}")
            continue
        with open(base_meta_file_full_path, "r") as g:
            command_tree_before = json.load(g)
        with open(diff_meta_file_full_path, "r") as g:
            command_tree_after = json.load(g)

        if command_tree_before.get("compat_version", None) \
                and check_meta_tool_compatibility(command_tree_before["compat_version"]):
            raise Exception("Please update your azure cli diff tool")
        if command_tree_after.get("compat_version", None) \
                and check_meta_tool_compatibility(command_tree_after["compat_version"]):
            raise Exception("Please update your azure cli diff tool")
        expand_deprecate_obj(command_tree_before)
        expand_deprecate_obj(command_tree_after)
        diff = DeepDiff(command_tree_before, command_tree_after)
        if not diff:
            print(f"No meta diffs from version: {diff_version}/{base_meta_file} for module: {module_name}")
            continue
        detected_changes = MetaChangeDetect(diff, command_tree_before, command_tree_after)
        detected_changes.check_deep_diffs()
        diff_objs = detected_changes.export_meta_changes(only_break, "dict")
        mod_obj = {"module": module_name}
        for obj in diff_objs:
            obj.update(mod_obj)
            version_diffs.append(obj)
    meta_change_end = time.time()
    logger.info("meta file diffs using {} sec".format(meta_change_end - download_target_end))
    if output_type == "dict":
        return export_meta_changes_to_dict(version_diffs, version_diff_file)
    return export_meta_changes_to_csv(version_diffs, version_diff_file)
