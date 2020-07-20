import astroid

from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker

class ShowCommandChecker(BaseChecker):
    __implements__ = IAstroidChecker

    name = 'show-command'
    priority = -1
    msgs = {
        'E5001': (
            'Show command must use show_command or custom_show_command.',
            'show-command',
            'Please use show_command or custom_show_command.'
        ),
    }

    def __init__(self, linter=None):
        super(ShowCommandChecker, self).__init__(linter)

    def visit_call(self, node):
        try:
            if not (isinstance(node.args[0], astroid.node_classes.Const) and node.args[0].value == 'show'):
                return
            if node.func.attrname == 'command' or node.func.attrname == 'custom_command':
                self.add_message(
                    'show-command', node=node,
                )
        except:
            return

def register(linter):
    linter.register_checker(ShowCommandChecker(linter))
