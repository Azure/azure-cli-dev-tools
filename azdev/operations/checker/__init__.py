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


def cmp_command_meta(base_meta_path, diff_meta_path):
    "todo: check file path here"
    start = time.time()
    # display('Loading command meta files...')
    with open(base_meta_path, "r") as g:
        command_tree_before = json.load(g)
    with open(diff_meta_path, "r") as g:
        command_tree_after = json.load(g)
    stop = time.time()
    # logger.info('Command meta files loaded in %i sec', stop - start)
    # display('Command meta files loaded in {0} sec'.format(stop - start))
    diff = DeepDiff(command_tree_before, command_tree_after)
    detected_changes = MetaChangeDetects(diff, command_tree_before, command_tree_after)
    detected_changes.check_deep_diffs()
    detected_changes.export_meta_changes_to_json()
    return detected_changes.export_meta_changes()

