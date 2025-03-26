# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------
# pylint: disable=line-too-long

# NOTE: The version update rules in this doc comply with the doc below
# https://github.com/Azure/azure-cli/blob/release/doc/extensions/versioning_guidelines.md

from packaging.version import parse
from knack.util import CLIError
from azure_cli_diff_tool.utils import DiffLevel
from azdev.operations.constant import (PREVIEW_INIT_SUFFIX, VERSION_MAJOR_TAG, VERSION_MINOR_TAG,
                                       VERSION_PATCH_TAG, VERSION_STABLE_TAG, VERSION_PREVIEW_TAG, VERSION_PRE_TAG,
                                       CLI_EXTENSION_INDEX_URL)


class ModuleVersion:

    def __init__(self, parse_version):
        self.major = parse_version.major
        self.minor = parse_version.minor
        self.patch = parse_version.micro
        self.pre = parse_version.pre
        self.pre_num = parse_version.pre and parse_version.pre[1]

    def init_stable_version(self):
        self.major = 1
        self.minor = 0
        self.patch = 0
        self.pre = None
        self.pre_num = 0

    def init_preview_version(self):
        self.major = 1
        self.minor = 0
        self.patch = 0
        self.pre = "b"
        self.pre_num = 1

    def __str__(self):
        version_arr = [self.major, ".", self.minor, ".", self.patch]
        if self.pre:
            version_arr.append(self.pre)
            version_arr.append(self.pre_num)
        return "".join([str(item) for item in version_arr])


# pylint: disable=too-many-instance-attributes
class VersionUpgradeMod:

    def __init__(self, module_name, current_version, is_preview, is_experimental,
                 meta_diff_before, meta_diff_after, next_version_pre_tag=None, next_version_segment_tag=None):
        self.module_name = module_name
        try:
            self.version = parse(current_version)
        except Exception as e:
            raise ValueError("Invalid version: {0} cause {1}".format(current_version, str(e)))
        self.is_preview = bool(is_preview or is_experimental or (self.version.pre and self.version.pre[0] in ["a", "b"]))
        self.has_preview_tag = is_preview
        self.has_exp_tag = is_experimental
        # x.x.x + (isPreview/isExperimental: True)
        # the versioning update rule for previous deprecated preview pattern is as following:
        # 1) 1.0.4 + isPreview: true -> stable: increase minor num to 1.1.0 + no preview tag
        # 2) 1.0.4 + isPreview: true -> preview: increase patch num to 1.0.5b1 + preview tag
        self.is_preview_deprecate_pattern = bool((is_preview or is_experimental) and not self.version.pre)
        self.version_raw = current_version
        self.norm_versions()
        self.base_meta_file = meta_diff_before
        self.diff_meta_file = meta_diff_after
        self.next_version_pre_tag = next_version_pre_tag and next_version_pre_tag.lower()
        self.next_version_segment_tag = next_version_segment_tag and next_version_segment_tag.lower()
        self.diffs = []
        self.init_version_diffs()
        self.init_version_pre_tag()
        self.next_version = ModuleVersion(self.version)
        self.last_stable_major = float('inf')
        self.pkg_name = self.module_name
        self.parse_pkg_name()
        self.parse_last_stable_major()

    def norm_versions(self):
        if not self.is_preview:
            return
        version_pre = self.version.pre
        if version_pre is None:
            self.version_raw += PREVIEW_INIT_SUFFIX
            try:
                self.version = parse(self.version_raw)
            except Exception as e:
                raise ValueError("Invalid version: {0} cause {1}".format(self.version_raw, str(e)))

    def init_version_diffs(self):
        from azure_cli_diff_tool import meta_diff
        meta_diffs = meta_diff(self.base_meta_file, self.diff_meta_file, output_type="dict")
        if meta_diffs:
            self.diffs = meta_diffs

    def init_version_pre_tag(self):
        """
        use next version pre tag if user inputs
        otherwise, consistent with the preview tag
        """
        if self.next_version_pre_tag is not None:
            return

        if self.is_preview:
            self.next_version_pre_tag = VERSION_PREVIEW_TAG
        else:
            self.next_version_pre_tag = VERSION_STABLE_TAG

    def update_next_version(self):
        if self.next_version_pre_tag == VERSION_STABLE_TAG:
            self.next_version.pre = None
            self.next_version.pre_num = 0
        elif self.next_version_pre_tag == VERSION_PREVIEW_TAG:
            self.next_version.pre = "b"
            self.next_version.pre_num = (self.version.pre and self.version.pre[1]) or 1
        else:
            raise ValueError("Unsupported pre tag: {0}".format(self.next_version_pre_tag))

        if self.version.major < 1:
            # for version starting with 0.x.x, norm them to first stable/preview version
            if self.next_version_pre_tag == VERSION_STABLE_TAG:
                self.next_version.init_stable_version()
            else:
                self.next_version.init_preview_version()
            return

        if self.next_version_pre_tag == VERSION_STABLE_TAG and self.is_preview:
            # normal case: 2.0.0bN -> stable > 2.0.0
            if self.is_preview_deprecate_pattern:
                # old preview tag pattern
                # 1.0.5 + isPreview: true -> stable -> 1.1.0
                self.next_version.minor = self.version.minor + 1
                self.next_version.patch = 0
            return

        if self.next_version_segment_tag:
            if self.next_version_segment_tag == VERSION_MAJOR_TAG:
                self.next_version.major = self.version.major + 1
                self.next_version.minor = 0
                self.next_version.patch = 0
                self.next_version.pre_num = 1
            elif self.next_version_segment_tag == VERSION_MINOR_TAG:
                self.next_version.minor = self.version.minor + 1
                self.next_version.patch = 0
                self.next_version.pre_num = 1
            elif self.next_version_segment_tag == VERSION_PATCH_TAG:
                self.next_version.patch = self.version.micro + 1
                self.next_version.pre_num = 1
            elif self.next_version_segment_tag == VERSION_PRE_TAG:
                self.next_version.pre_num = (self.version.pre and self.version.pre[1] or 0) + 1
            else:
                raise ValueError("Unsupported segment tag: {0}".format(self.next_version_segment_tag))
            return

        self.update_version_from_differs()

    def update_version_from_differs(self):
        found_break = False
        for item in self.diffs:
            if item["diff_level"] == DiffLevel.BREAK.value:
                found_break = True
                break
        if found_break:
            if self.next_version_pre_tag == VERSION_PREVIEW_TAG and self.is_preview and self.last_stable_major < self.version.major:
                # refer to rule: https://github.com/Azure/azure-cli/blob/release/doc/extensions/versioning_guidelines.md#notes-1
                if self.is_preview_deprecate_pattern:
                    # 1.1.0 + isPreview:True -> preview -> 1.1.1b1
                    # if 1.1.0b2, then version cannot upgrade in core
                    self.next_version.patch = self.version.micro + 1
                    self.next_version.pre_num = 1
                else:
                    self.next_version.pre_num = self.version.pre[1] + 1
            else:
                self.next_version.major = self.version.major + 1
                self.next_version.minor = 0
                self.next_version.patch = 0
                if self.is_preview:
                    self.next_version.pre_num = 1
        elif len(self.diffs) > 0:
            if self.is_preview:
                if self.is_preview_deprecate_pattern:
                    # 1.1.0 + isPreview:True -> preview -> 1.1.1b1
                    # if 1.1.0b2, then version cannot upgrade in core
                    self.next_version.patch = self.version.micro + 1
                    self.next_version.pre_num = 1
                else:
                    self.next_version.pre_num = self.version.pre[1] + 1
            else:
                self.next_version.minor = self.version.minor + 1
                self.next_version.patch = 0
        else:
            if self.is_preview:
                if self.is_preview_deprecate_pattern:
                    # 1.1.0 + isPreview:True -> preview -> 1.1.1b1
                    # if 1.1.0b2, then version cannot upgrade in core
                    self.next_version.patch = self.version.micro + 1
                    self.next_version.pre_num = 1
                else:
                    self.next_version.pre_num = self.version.pre[1] + 1
            else:
                self.next_version.patch = self.version.micro + 1

    @staticmethod
    def find_max_version(version_datas):
        max_stable_major = -1
        has_stable = False
        for item in version_datas:
            try:
                version_parse = parse(item["metadata"]["version"])
            except Exception as e:
                raise ValueError(str(e))
            if version_parse.pre is None and not item["metadata"].get("azext.isExperimental", False) \
                    and not item["metadata"].get("azext.isPreview", False):
                max_stable_major = max(version_parse.major, max_stable_major)
                has_stable = True
        return has_stable, max_stable_major

    def parse_pkg_name(self):
        from azdev.operations.extensions import show_extension
        try:
            self.pkg_name = show_extension(self.module_name)["pkg_name"]
        except CLIError:
            pass

    def parse_last_stable_major(self):
        import requests
        try:
            response = requests.get(CLI_EXTENSION_INDEX_URL)
            extension_data = response.json()
            if self.pkg_name not in extension_data["extensions"]:
                return
            has_stable, max_stable_major = self.find_max_version(
                extension_data["extensions"][self.pkg_name])
            if has_stable:
                self.last_stable_major = max_stable_major
            else:
                self.last_stable_major = 0
        except Exception as e:
            raise ValueError(str(e))

    def gen_preview_exp_tags(self, res_dict):
        """
        if next_version is preview: due to doc generation requirement, preview tag is needed
        1. preview tag need to be reserved which had previous preview tag, nothing to do
        2. preview tag need to be added if previous version does not have preview tag

        if next_version is stable:
        remove previous existed preview tag

        exp tag should be removed for stable/preview
        """
        if self.has_exp_tag:
            res_dict["exp_tag"] = "remove"
        if self.next_version.pre:
            if not self.has_preview_tag:
                res_dict["preview_tag"] = "add"
        else:
            if self.has_preview_tag:
                res_dict["preview_tag"] = "remove"

    def format_outputs(self):
        result = {
            "version": str(self.next_version),
            "is_stable": self.next_version.pre is None
        }
        self.gen_preview_exp_tags(result)
        return result
