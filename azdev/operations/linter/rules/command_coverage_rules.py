# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from ..rule_decorators import CommandCoverageRule
from ..linter import RuleError, LinterSeverity


@CommandCoverageRule(LinterSeverity.HIGH)
def missing_command_coverage(linter):
    if not linter.get_command_coverage():
        raise RuleError('Missing Command Coverage')