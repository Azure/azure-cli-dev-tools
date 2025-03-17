# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import json
import tempfile
import unittest
from unittest import mock

from microsoft_security_utilities_secret_masker import RegexPattern
from azdev.operations.secret import scan_secrets, mask_secrets
from azdev.utilities.config import get_azdev_config_dir


# pylint: disable=line-too-long, anomalous-backslash-in-string
class TestScanAndMaskSecrets(unittest.TestCase):
    def test_scan_raw_string(self):
        test_data = "This is a test string without any secrets."
        result = scan_secrets(data=test_data)
        self.assertFalse(result['secrets_detected'])
        custom_pattern = {
            "Include": [
                {
                    "Pattern": "secret",
                    "Name": "AdditionalPattern"
                }
            ]
        }
        result = scan_secrets(data=test_data, custom_pattern=json.dumps(custom_pattern))
        self.assertTrue(result['secrets_detected'])
        self.assertEqual(len(result['scan_results']['raw_data']), 1)
        self.assertEqual(result['scan_results']['raw_data'][0]['secret_name'], 'AdditionalPattern')

        regex_pattern1 = RegexPattern(r'(?P<refine>[\w.%#+-]+)(%40|@)([a-z0-9.-]*.[a-z]{2,})', '000', 'EmailAddress')
        regex_pattern2 = RegexPattern('(?i)(?:^|[?;&])(?:dsas_secret|sig)=(?P<refine>[0-9a-z\\/+%]{43,129}(?:=|%3d))', '001', 'LooseSasSecret')
        with mock.patch("azdev.operations.secret._load_built_in_regex_patterns", return_value=(regex_pattern1, regex_pattern2)):
            test_data2 = "This is a test string with email fooabc@gmail.com and sas sv=2022-11-02&sr=c&sig=a9Y5mpQgKUiiPzHFNdDm53Na6UndTrNMCsRZd6b2oV4%3D"
            result = scan_secrets(data=test_data2)
            self.assertTrue(result['secrets_detected'])
            self.assertEqual(len(result['scan_results']['raw_data']), 2)
            custom_pattern = {
                "Exclude": [
                    {
                        "Id": '000',
                        "Name": 'EmailAddress'
                    }
                ]
            }
            result = scan_secrets(data=test_data2, custom_pattern=json.dumps(custom_pattern))
            self.assertTrue(result['secrets_detected'])
            self.assertEqual(len(result['scan_results']['raw_data']), 1)
            self.assertEqual(result['scan_results']['raw_data'][0]['secret_name'], 'LooseSasSecret')
            self.assertEqual(result['scan_results']['raw_data'][0]['secret_value'], 'a9Y5mpQgKUiiPzHFNdDm53Na6UndTrNMCsRZd6b2oV4%3D')

            try:
                result = scan_secrets(data=test_data2, save_scan_result=True)
                self.assertTrue(result['secrets_detected'])
                self.assertIn('scan_result_path', result)
                result_folder = os.path.join(get_azdev_config_dir(), 'scan_results')
                self.assertIn(result_folder, result['scan_result_path'])
            finally:
                if result.get('scan_result_path', ''):
                    os.remove(result['scan_result_path'])

    def test_scan_file(self):
        file_folder = os.path.join(os.path.dirname(__file__), 'files')
        file_sub_folder = os.path.join(file_folder, 'subdir')
        simple_string_file = os.path.join(file_folder, 'simple_string.txt')
        info_json_file = os.path.join(file_sub_folder, 'info.json')

        result = scan_secrets(file_path=simple_string_file)
        self.assertFalse(result['secrets_detected'])
        custom_pattern = {
            "Include": [
                {
                    "Pattern": "secret",
                    "Name": "AdditionalPattern"
                }
            ]
        }
        result = scan_secrets(file_path=simple_string_file, custom_pattern=json.dumps(custom_pattern))
        self.assertTrue(result['secrets_detected'])
        self.assertEqual(len(result['scan_results'][simple_string_file]), 1)
        self.assertEqual(result['scan_results'][simple_string_file][0]['secret_name'], 'AdditionalPattern')

        regex_pattern1 = RegexPattern(r'(?P<refine>[\w.%#+-]+)(%40|@)([a-z0-9.-]*.[a-z]{2,})', '000', 'EmailAddress')
        regex_pattern2 = RegexPattern('(?i)(?:^|[?;&])(?:dsas_secret|sig)=(?P<refine>[0-9a-z\\/+%]{43,129}(?:=|%3d))', '001', 'LooseSasSecret')
        with mock.patch("azdev.operations.secret._load_built_in_regex_patterns", return_value=(regex_pattern1, regex_pattern2)):
            result = scan_secrets(file_path=info_json_file)
            self.assertTrue(result['secrets_detected'])
            self.assertEqual(len(result['scan_results'][info_json_file]), 2)
            custom_pattern = {
                "Exclude": [
                    {
                        "Id": '000',
                        "Name": 'EmailAddress'
                    }
                ]
            }
            result = scan_secrets(file_path=info_json_file, custom_pattern=json.dumps(custom_pattern))
            self.assertTrue(result['secrets_detected'])
            self.assertEqual(len(result['scan_results'][info_json_file]), 1)
            self.assertEqual(result['scan_results'][info_json_file][0]['secret_name'], 'LooseSasSecret')
            self.assertEqual(result['scan_results'][info_json_file][0]['secret_value'], 'a9Y5mpQgKUiiPzHFNdDm53Na6UndTrNMCsRZd6b2oV4%3D')

    def test_scan_directory(self):
        file_folder = os.path.join(os.path.dirname(__file__), 'files')
        file_sub_folder = os.path.join(file_folder, 'subdir')
        email_string_file = os.path.join(file_folder, 'email_string.txt')
        info_json_file = os.path.join(file_sub_folder, 'info.json')

        result = scan_secrets(directory_path=file_folder)
        self.assertFalse(result['secrets_detected'])

        custom_pattern = {
            "Include": [
                {
                    "Pattern": r"(?P<refine>[\w.%#+-]+)(%40|@)([a-z0-9.-]*.[a-z]{2,})",
                    "Name": "EmailAddress"
                }
            ]
        }
        result = scan_secrets(directory_path=file_folder, custom_pattern=json.dumps(custom_pattern))
        self.assertTrue(result['secrets_detected'])
        self.assertEqual(len(result['scan_results'][email_string_file]), 1)
        self.assertEqual(result['scan_results'][email_string_file][0]['secret_name'], 'EmailAddress')
        self.assertNotIn(info_json_file, result['scan_results'])

        result = scan_secrets(directory_path=file_folder, recursive=True, custom_pattern=json.dumps(custom_pattern))
        self.assertTrue(result['secrets_detected'])
        self.assertEqual(len(result['scan_results'][email_string_file]), 1)
        self.assertEqual(result['scan_results'][email_string_file][0]['secret_name'], 'EmailAddress')
        self.assertEqual(len(result['scan_results'][info_json_file]), 1)
        self.assertEqual(result['scan_results'][info_json_file][0]['secret_name'], 'EmailAddress')

        result = scan_secrets(directory_path=file_folder, recursive=True, include_pattern=['*.json'], custom_pattern=json.dumps(custom_pattern))
        self.assertTrue(result['secrets_detected'])
        self.assertNotIn(email_string_file, result['scan_results'])
        self.assertIn(info_json_file, result['scan_results'])

        result = scan_secrets(directory_path=file_folder, recursive=True, exclude_pattern=['*.json'], custom_pattern=json.dumps(custom_pattern))
        self.assertTrue(result['secrets_detected'])
        self.assertIn(email_string_file, result['scan_results'])
        self.assertNotIn(info_json_file, result['scan_results'])

    def test_mask(self):
        test_data = "This is a test string with email fooabc@gmail.com and sas sv=2022-11-02&sr=c&sig=a9Y5mpQgKUiiPzHFNdDm53Na6UndTrNMCsRZd6b2oV4%3D"
        result = mask_secrets(data=test_data, yes=True)
        self.assertFalse(result['mask'])
        custom_pattern = {
            "Include": [
                {
                    "Pattern": r"(?P<refine>[\w.%#+-]+)(%40|@)([a-z0-9.-]*.[a-z]{2,})",
                    "Name": "EmailAddress"
                }
            ]
        }
        tmpdir = tempfile.mkdtemp()
        scan_result_path = os.path.join(tmpdir, 'test_scan_result.json')
        try:
            result = mask_secrets(data=test_data, custom_pattern=json.dumps(custom_pattern), save_scan_result=True, scan_result_path=scan_result_path, yes=True)
            self.assertTrue(os.path.exists(scan_result_path))
            self.assertEqual(result['data'], 'This is a test string with email ***@gmail.com and sas sv=2022-11-02&sr=c&sig=a9Y5mpQgKUiiPzHFNdDm53Na6UndTrNMCsRZd6b2oV4%3D')

            result = mask_secrets(data=test_data, saved_scan_result_path=scan_result_path, yes=True)
            self.assertEqual(result['data'], 'This is a test string with email ***@gmail.com and sas sv=2022-11-02&sr=c&sig=a9Y5mpQgKUiiPzHFNdDm53Na6UndTrNMCsRZd6b2oV4%3D')

            result = mask_secrets(data=test_data, saved_scan_result_path=scan_result_path, redaction_type='FIXED_LENGTH', yes=True)
            self.assertEqual(result['data'], 'This is a test string with email ******@gmail.com and sas sv=2022-11-02&sr=c&sig=a9Y5mpQgKUiiPzHFNdDm53Na6UndTrNMCsRZd6b2oV4%3D')

            result = mask_secrets(data=test_data, saved_scan_result_path=scan_result_path, redaction_type='SECRET_NAME', yes=True)
            self.assertEqual(result['data'], 'This is a test string with email EmailAddress@gmail.com and sas sv=2022-11-02&sr=c&sig=a9Y5mpQgKUiiPzHFNdDm53Na6UndTrNMCsRZd6b2oV4%3D')
        finally:
            if os.path.exists(scan_result_path):
                os.remove(scan_result_path)
            os.removedirs(tmpdir)
