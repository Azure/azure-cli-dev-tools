# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from ..rule_decorators import CommandCoverageRule
from ..linter import RuleError, LinterSeverity


@CommandCoverageRule(LinterSeverity.HIGH)
def missing_command_test_coverage(linter):
    exec_state, violations = linter.get_command_test_coverage()
    if not exec_state:
        violation_msg = "\n\t".join(violations)
        raise RuleError(violation_msg + "\n")


@CommandCoverageRule(LinterSeverity.MEDIUM)
def missing_parameter_test_coverage(linter):
    exec_state, violations = linter.get_parameter_test_coverage()
    if not exec_state:
        violation_msg = "\n\t".join(violations)
        raise RuleError(violation_msg + "\n")
