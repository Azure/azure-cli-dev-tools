# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import configparser
import unittest
from unittest import mock


class TestConfigFilePath(unittest.TestCase):
    def test_black_config_without_setup(self):
        mocked_config = configparser.ConfigParser()
        mocked_config.add_section("cli")
        mocked_config.set("cli", "repo_path", "")
        mocked_config.add_section("ext")
        mocked_config.set("ext", "repo_paths", "")


    def test_black_config_with_partially_setup(self):
        cli_repo_path = "~/Azure/azure-cli"
        mocked_config = configparser.ConfigParser()
        mocked_config.add_section("cli")
        mocked_config.set("cli", "repo_path", cli_repo_path)
        mocked_config.add_section("ext")
        mocked_config.set("ext", "repo_paths", "")

    def test_black_config_with_all_setup(self):
        cli_repo_path = "~/Azure/azure-cli"
        ext_repo_path = "~/Azure/azure-cli-extensions"
        mocked_config = configparser.ConfigParser()
        mocked_config.add_section("cli")
        mocked_config.set("cli", "repo_path", cli_repo_path)
        mocked_config.add_section("ext")
        mocked_config.set("ext", "repo_paths", ext_repo_path)
