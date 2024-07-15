# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------
import astroid

from pylint.checkers import BaseChecker


class ShowCommandChecker(BaseChecker):

    name = 'show-command'
    priority = -1
    msgs = {
        'E5001': (
            'Show command must use show_command or custom_show_command.',
            'show-command',
            'Please use show_command or custom_show_command.'
        ),
    }

    def visit_call(self, node):
        try:
            if not (isinstance(node.args[0], astroid.node_classes.Const) and node.args[0].value == 'show'):
                return
            if node.func.attrname in ('command', 'custom_command'):
                self.add_message(
                    'show-command', node=node,
                )
        except IndexError:
            return


def register(linter):
    linter.register_checker(ShowCommandChecker(linter))
