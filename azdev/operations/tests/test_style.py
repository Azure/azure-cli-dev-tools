# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import configparser
import unittest
from unittest import mock

from azdev.operations.style import _config_file_path


class TestConfigFilePath(unittest.TestCase):
    def test_unsupported_code_style_checker(self):
        with self.assertRaises(ValueError):
            _config_file_path(style_type="unknown")

    def test_pylint_config_without_setup(self):
        mocked_config = configparser.ConfigParser()
        mocked_config.add_section("cli")
        mocked_config.set("cli", "repo_path", "")
        mocked_config.add_section("ext")
        mocked_config.set("ext", "repo_paths", "")

        with mock.patch("azdev.operations.style.get_azdev_config", return_value=mocked_config):
            r = _config_file_path(style_type="pylint")
            self.assertTrue(r[0].endswith("/config_files/cli_pylintrc"))
            self.assertTrue(r[1].endswith("/config_files/ext_pylintrc"))

    def test_pylint_config_with_partially_setup(self):
        cli_repo_path = "~/Azure/azure-cli"
        mocked_config = configparser.ConfigParser()
        mocked_config.add_section("cli")
        mocked_config.set("cli", "repo_path", cli_repo_path)
        mocked_config.add_section("ext")
        mocked_config.set("ext", "repo_paths", "")

        with mock.patch("azdev.operations.style.get_azdev_config", return_value=mocked_config):
            r = _config_file_path(style_type="pylint")
            self.assertEqual(r[0], cli_repo_path + "/pylintrc")
            self.assertTrue(r[1].endswith("/config_files/ext_pylintrc"))

    def test_pylint_config_with_all_setup(self):
        cli_repo_path = "~/Azure/azure-cli"
        ext_repo_path = "~/Azure/azure-cli-extensions"
        mocked_config = configparser.ConfigParser()
        mocked_config.add_section("cli")
        mocked_config.set("cli", "repo_path", cli_repo_path)
        mocked_config.add_section("ext")
        mocked_config.set("ext", "repo_paths", ext_repo_path)

        with mock.patch("azdev.operations.style.get_azdev_config", return_value=mocked_config):
            r = _config_file_path()
            self.assertEqual(r[0], cli_repo_path + "/pylintrc")
            self.assertTrue(r[1], "/pylintrc")

    def test_flake8_config_wihtout_setup(self):
        mocked_config = configparser.ConfigParser()
        mocked_config.add_section("cli")
        mocked_config.set("cli", "repo_path", "")
        mocked_config.add_section("ext")
        mocked_config.set("ext", "repo_paths", "")

        with mock.patch("azdev.operations.style.get_azdev_config", return_value=mocked_config):
            r = _config_file_path(style_type="flake8")
            self.assertTrue(r[0].endswith("/config_files/cli.flake8"))
            self.assertTrue(r[1].endswith("/config_files/ext.flake8"))

    def test_flake8_config_with_partially_setup(self):
        ext_repo_path = "~/Azure/azure-cli-extensions"

        mocked_config = configparser.ConfigParser()
        mocked_config.add_section("cli")
        mocked_config.set("cli", "repo_path", "")
        mocked_config.add_section("ext")
        mocked_config.set("ext", "repo_paths", ext_repo_path)

        with mock.patch("azdev.operations.style.get_azdev_config", return_value=mocked_config):
            r = _config_file_path(style_type="flake8")
            self.assertTrue(r[0].endswith("/config_files/cli.flake8"))
            self.assertTrue(r[1].endswith(ext_repo_path + "/.flake8"))

    def test_flake9_config_with_all_setup(self):
        cli_repo_path = "~/Azure/azure-cli"
        ext_repo_path = "~/Azure/azure-cli-extensions"

        mocked_config = configparser.ConfigParser()
        mocked_config.add_section("cli")
        mocked_config.set("cli", "repo_path", cli_repo_path)
        mocked_config.add_section("ext")
        mocked_config.set("ext", "repo_paths", ext_repo_path)

        with mock.patch("azdev.operations.style.get_azdev_config", return_value=mocked_config):
            r = _config_file_path(style_type="flake8")
            self.assertTrue(r[0].endswith(cli_repo_path + "/.flake8"))
            self.assertTrue(r[1].endswith(ext_repo_path + "/.flake8"))
