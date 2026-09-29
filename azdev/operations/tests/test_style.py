# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import configparser
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from azdev.operations.style import _config_file_path


class TestConfigFilePath(unittest.TestCase):
    def setUp(self):
        # The fixture lives until unittest runs registered cleanups after the test.
        directory = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.cli_repo = self.root / 'azure-cli'
        self.ext_repo = self.root / 'azure-cli-extensions'
        for repo in (self.cli_repo, self.ext_repo):
            repo.mkdir()
            for name in ('pylintrc', '.flake8'):
                (repo / name).touch()
        patcher = mock.patch('azdev.operations.style.get_azdev_config_dir',
                             return_value=str(self.root / 'config'))
        patcher.start()
        self.addCleanup(patcher.stop)

    def assert_default_config(self, actual, name):
        self.assertEqual(actual, str(self.root / 'config' / 'config_files' / name))

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
            self.assert_default_config(r[0], 'cli_pylintrc')
            self.assert_default_config(r[1], 'ext_pylintrc')

    def test_pylint_config_with_partially_setup(self):
        cli_repo_path = str(self.cli_repo)
        mocked_config = configparser.ConfigParser()
        mocked_config.add_section("cli")
        mocked_config.set("cli", "repo_path", cli_repo_path)
        mocked_config.add_section("ext")
        mocked_config.set("ext", "repo_paths", "")

        with mock.patch("azdev.operations.style.get_azdev_config", return_value=mocked_config):
            r = _config_file_path(style_type="pylint")
            self.assertEqual(r[0], os.path.join(cli_repo_path, 'pylintrc'))
            self.assert_default_config(r[1], 'ext_pylintrc')

    def test_pylint_config_with_all_setup(self):
        cli_repo_path = str(self.cli_repo)
        ext_repo_path = str(self.ext_repo)
        mocked_config = configparser.ConfigParser()
        mocked_config.add_section("cli")
        mocked_config.set("cli", "repo_path", cli_repo_path)
        mocked_config.add_section("ext")
        mocked_config.set("ext", "repo_paths", ext_repo_path)

        with mock.patch("azdev.operations.style.get_azdev_config", return_value=mocked_config):
            r = _config_file_path()
            self.assertEqual(r[0], os.path.join(cli_repo_path, 'pylintrc'))
            self.assertEqual(r[1], os.path.join(ext_repo_path, 'pylintrc'))

    def test_flake8_config_wihtout_setup(self):
        mocked_config = configparser.ConfigParser()
        mocked_config.add_section("cli")
        mocked_config.set("cli", "repo_path", "")
        mocked_config.add_section("ext")
        mocked_config.set("ext", "repo_paths", "")

        with mock.patch("azdev.operations.style.get_azdev_config", return_value=mocked_config):
            r = _config_file_path(style_type="flake8")
            self.assert_default_config(r[0], 'cli.flake8')
            self.assert_default_config(r[1], 'ext.flake8')

    def test_flake8_config_with_partially_setup(self):
        ext_repo_path = str(self.ext_repo)

        mocked_config = configparser.ConfigParser()
        mocked_config.add_section("cli")
        mocked_config.set("cli", "repo_path", "")
        mocked_config.add_section("ext")
        mocked_config.set("ext", "repo_paths", ext_repo_path)

        with mock.patch("azdev.operations.style.get_azdev_config", return_value=mocked_config):
            r = _config_file_path(style_type="flake8")
            self.assert_default_config(r[0], 'cli.flake8')
            self.assertEqual(r[1], os.path.join(ext_repo_path, '.flake8'))

    def test_flake8_config_with_all_setup(self):
        cli_repo_path = str(self.cli_repo)
        ext_repo_path = str(self.ext_repo)

        mocked_config = configparser.ConfigParser()
        mocked_config.add_section("cli")
        mocked_config.set("cli", "repo_path", cli_repo_path)
        mocked_config.add_section("ext")
        mocked_config.set("ext", "repo_paths", ext_repo_path)

        with mock.patch("azdev.operations.style.get_azdev_config", return_value=mocked_config):
            r = _config_file_path(style_type="flake8")
            self.assertEqual(r[0], os.path.join(cli_repo_path, '.flake8'))
            self.assertEqual(r[1], os.path.join(ext_repo_path, '.flake8'))

    def test_style_with_all_setup_but_not_exist(self):
        cli_repo_path = str(self.root / 'missing-cli')
        ext_repo_path = str(self.root / 'missing-extensions')
        mocked_config = configparser.ConfigParser()
        mocked_config.add_section("cli")
        mocked_config.set("cli", "repo_path", cli_repo_path)
        mocked_config.add_section("ext")
        mocked_config.set("ext", "repo_paths", ext_repo_path)

        with mock.patch("azdev.operations.style.get_azdev_config", return_value=mocked_config):
            r1 = _config_file_path(style_type="flake8")
            r2 = _config_file_path(style_type="pylint")
            self.assert_default_config(r1[0], 'cli.flake8')
            self.assert_default_config(r1[1], 'ext.flake8')
            self.assert_default_config(r2[0], 'cli_pylintrc')
            self.assert_default_config(r2[1], 'ext_pylintrc')
