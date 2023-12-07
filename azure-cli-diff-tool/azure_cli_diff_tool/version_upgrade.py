# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import json
from packaging.version import parse
from . import meta_diff


class VersionUpgradeMod:

    def __init__(self, current_version, is_preview, is_experimental,
                 meta_diff_before, meta_diff_after, version_pre_update=False, segment_tag=None):
        self.version = parse(current_version)
        self.version_raw = current_version
        self.base_meta_file = meta_diff_before
        self.diff_meta_file = meta_diff_after
        self.version_pre_update = version_pre_update
        self.segment_tag = segment_tag
        self.diffs = []
        self.is_preview_before = bool(is_preview or is_experimental or self.version.pre[0] in ["a", "b"])
        self.init_version_diffs()

    def init_version_diffs(self):
        self.diffs = meta_diff(self.base_meta_file, self.diff_meta_file)

    def update_major(self):
        if self.segment_tag and self.segment_tag != "major":
            return
        found_break = False
        for item in self.diffs:
            if item.diff_level == "3":
                found_break = True
                break
        if found_break or self.segment_tag == "major":
            self.version.release[0] += 1

    def update_minor(self):
        if self.segment_tag and self.segment_tag != "minor":
            return
        if self.segment_tag == "minor":
            self.version.release[1] += 1
        elif len(self.diffs) > 0 and not self.is_preview_before:
            self.version.release[1] += 1

    def update_patch(self):
        if self.segment_tag and self.segment_tag != "patch":
            return
        if self.segment_tag == "patch":
            self.version.release[2] += 1
        elif len(self.diffs) > 0 and not self.is_preview_before:
            self.version.release[2] += 1

    def update_pre(self):
        if not self.version_pre_update:
            return
        if self.is_preview_before:
            self.version.pre = None
        else:
            self.version.pre = ("b", 1)

    def update_pre_number(self):
        if not self.is_preview_before and not self.version_pre_update:
            return
        if not self.is_preview_before:
            return
        self.version.pre[1] += 1
