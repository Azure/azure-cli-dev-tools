# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import time, json
from deepdiff import DeepDiff
from .meta_changes import MetaChangeDetects

from knack.log import get_logger
from azdev.utilities import display

logger = get_logger(__name__)


def cmp_command_meta(table_path, diff_table_path):
    "todo: check file path here"
    start = time.time()
    display('Loading command meta files...')
    with open(table_path, "r") as g:
        command_tree_before = json.load(g)
    with open(diff_table_path, "r") as g:
        command_tree_after = json.load(g)
    stop = time.time()
    logger.info('Command meta files loaded in %i sec', stop - start)
    display('Command meta files loaded in {0} sec'.format(stop - start))
    diff = DeepDiff(command_tree_before, command_tree_after)
    print("dict key remove: ")
    if diff.get("dictionary_item_removed", None):
        dict_item_remove = diff["dictionary_item_removed"]
        for item in dict_item_remove:
            print(item)
    print("dict key add: ")
    if diff.get("dictionary_item_added", None):
        dict_item_add = diff["dictionary_item_added"]
        for item in dict_item_add:
            print(item)
    print("list key remove: ")
    if diff.get("iterable_item_removed", None):
        list_item_remove = diff["iterable_item_removed"]
        for key, value in list_item_remove.items():
            print("key: ", key)
            print("value: ", value)
    print("list key add: ")
    if diff.get("iterable_item_added", None):
        list_item_add = diff["iterable_item_added"]
        for key, value in list_item_add.items():
            print("key: ", key)
            print("value: ", value)
    print("values changed: ")
    if diff.get("values_changed", None):
        value_changes = diff["values_changed"]
        for key, value in value_changes.items():
            print("key: ", key)
            print("value: ", value)
    detected_changes = MetaChangeDetects(diff, command_tree_before, command_tree_after)
    detected_changes.check_deep_diffs()
    detected_changes.export_meta_changes()

