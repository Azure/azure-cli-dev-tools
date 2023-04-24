# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import time, json, os
from deepdiff import DeepDiff
from .operation import MetaChangeDetects
from azdev.utilities import display
from .util import export_meta_changes_to_json

from knack.log import get_logger

logger = get_logger(__name__)


def cmp_command_meta(base_meta_path, diff_meta_path, only_break=False, as_text=False, as_obj=False,
                     as_tree=False, output_file=None):
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
    ret_txt, ret_obj, ret_mod = detected_changes.export_meta_changes(only_break, as_tree)
    result = []
    if as_text:
        result = ret_txt
    if as_obj:
        result = ret_obj
    if as_tree:
        result = ret_mod
    if output_file:
        export_meta_changes_to_json(result, output_file)
    else:
        return result


