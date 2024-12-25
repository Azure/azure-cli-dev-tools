# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from ..rule_decorators import ExtraCliLinterRule
from ..linter import RuleError, LinterSeverity

CMD_EXAMPLE_VIOLATE_MESSAGE = " cmd: `{}` should have as least {} examples, while {} detected"


@ExtraCliLinterRule(LinterSeverity.HIGH)
def missing_examples_from_added_command(linter):
    filtered_cmd_example = linter.check_examples_from_added_command()

    def format_cmd_example_violation_message(cmd_obj):
        return CMD_EXAMPLE_VIOLATE_MESSAGE.format(cmd_obj["cmd"], cmd_obj["min_example_count"],
                                                  cmd_obj["example_count"])
    if filtered_cmd_example:
        violation_msg = "Please check following cmd example violation messages: \n"
        violation_msg += "\n".join(list(map(format_cmd_example_violation_message, filtered_cmd_example)))
        raise RuleError(violation_msg + "\n")
