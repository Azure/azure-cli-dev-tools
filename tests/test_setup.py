# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import unittest

from azdev.utilities import test_cmd as cmd


class TestSetup(unittest.TestCase):

    def test_setup(self):
        from knack.prompting import NoTTYException

        with self.assertRaises(NoTTYException):
            cmd('setup')
