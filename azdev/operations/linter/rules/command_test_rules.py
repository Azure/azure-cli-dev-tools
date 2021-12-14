# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from ..rule_decorators import CommandTestRule
from ..linter import RuleError, LinterSeverity


@CommandTestRule(LinterSeverity.HIGH)
def missing_command_test(linter):
    if not linter.get_command_test():
        raise RuleError('Missing Command Test')