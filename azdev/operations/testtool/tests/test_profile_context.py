# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import unittest

from knack.util import CLIError

from azdev.operations.testtool.profile_context import ProfileContext


class TestProfileContext(unittest.TestCase):

    def test_profile_ok(self):
        target_profiles = ['latest', '2017-03-09-profile', '2018-03-01-hybrid', '2019-03-01-hybrid']

        for profile in target_profiles:
            with ProfileContext(profile):
                self.assertEqual(1, 1)

    def test_unsupported_profile(self):
        unknown_profile = 'unknown-profile'

        with self.assertRaises(CLIError):
            with ProfileContext(unknown_profile):
                pass

    def test_raise_inner_exception(self):
        with self.assertRaises(Exception):
            with ProfileContext('latest'):
                raise Exception('inner Exception') # pylint: disable=broad-except
