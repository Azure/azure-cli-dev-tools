# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import argparse
import tempfile
import unittest

from knack import CLI
from knack.arguments import ArgumentsContext, CLICommandArgument

from azdev.operations.command_change.custom import gen_command_meta

FLAG_ACTIONS = ["store_true", "store_false", "store_const", "count"]


class _OptionalValueAction(argparse.Action):  # pylint: disable=too-few-public-methods
    """Takes an optional value, like Azure CLI's three-state flags, so it isn't a flag."""

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


class _NoValueAction(argparse.Action):  # pylint: disable=too-few-public-methods
    """Registered with nargs=0, like core's action for --acquire-policy-token."""

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, True)


class _ValueAction(argparse.Action):  # pylint: disable=too-few-public-methods
    """Takes a value, like core's action for --change-reference."""

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


def _params(arguments):
    command_info = {
        "name": "test cmd",
        "is_aaz": False,
        "arguments": {argument.type.settings["dest"]: argument for argument in arguments},
    }
    return {para["name"]: para for para in gen_command_meta(command_info)["parameters"]}


class CommandMetaActionTestCase(unittest.TestCase):

    def setUp(self):
        config_dir = tempfile.TemporaryDirectory()  # pylint: disable=consider-using-with
        self.addCleanup(config_dir.cleanup)
        cli = CLI(cli_name="test", config_dir=config_dir.name)
        cli.invocation = cli.invocation_cls(cli_ctx=cli, parser_cls=cli.parser_cls,
                                            commands_loader_cls=cli.commands_loader_cls, help_cls=cli.help_cls)
        self.loader = cli.invocation.commands_loader
        self.loader.skip_applicability = True

    def _register(self, register):
        """Register arguments the way command modules do, so knack applies its action wrappers."""
        with ArgumentsContext(self.loader, "test cmd") as c:
            register(c)
        return [CLICommandArgument(dest, argtype=argtype)
                for dest, argtype in self.loader.argument_registry.arguments["test cmd"].items()]

    def test_flag_action_strings(self):
        arguments = [CLICommandArgument(action + "_flag", action=action) for action in FLAG_ACTIONS]
        params = _params(arguments)
        for action in FLAG_ACTIONS:
            self.assertEqual(params[action + "_flag"].get("action"), action)

    def test_flag_actions_wrapped_by_knack(self):
        def register(c):
            c.argument("preview_flag", action="store_true", is_preview=True)
            c.argument("experimental_flag", action="store_false", is_experimental=True)
            c.argument("deprecated_flag", action="store_true", deprecate_info=c.deprecate(hide=False))
            c.argument("deprecated_option_flag", action="store_false",
                       options_list=["--new-flag", c.deprecate(target="--old-flag", redirect="--new-flag")])
            c.argument("preview_const", action="store_const", const="value", is_preview=True)
            c.argument("deprecated_count", action="count", deprecate_info=c.deprecate(hide=False))

        arguments = self._register(register)
        for argument in arguments:
            action = argument.type.settings["action"]
            self.assertTrue(isinstance(action, type) and action.__module__ != "argparse",
                            f"{argument.type.settings['dest']} isn't a wrapper subclass: {action}")
        params = _params(arguments)
        self.assertEqual(params["preview_flag"].get("action"), "store_true")
        self.assertEqual(params["experimental_flag"].get("action"), "store_false")
        self.assertEqual(params["deprecated_flag"].get("action"), "store_true")
        self.assertEqual(params["deprecated_option_flag"].get("action"), "store_false")
        self.assertEqual(params["preview_const"].get("action"), "store_const")
        self.assertEqual(params["deprecated_count"].get("action"), "count")

    def test_custom_actions_that_take_no_value(self):
        def register(c):
            c.argument("acquire_policy_token", options_list=["--acquire-policy-token"],
                       action=_NoValueAction, nargs=0)
            c.argument("change_reference", options_list=["--change-reference"], action=_ValueAction)
            c.argument("preview_no_value", action=_NoValueAction, nargs=0, is_preview=True)
            c.argument("deprecated_no_value", action=_NoValueAction, nargs=0, deprecate_info=c.deprecate(hide=False))
            # nargs=0 doesn't replace a flag action that's already recorded
            c.argument("store_false_nargs_0", action="store_false", nargs=0)

        arguments = self._register(register)
        settings = {argument.type.settings["dest"]: argument.type.settings for argument in arguments}
        for name in ("preview_no_value", "deprecated_no_value"):
            action = settings[name]["action"]
            self.assertTrue(action is not _NoValueAction and issubclass(action, _NoValueAction), name)
        params = _params(arguments)
        self.assertEqual(params["acquire_policy_token"].get("action"), "store_true")
        self.assertNotIn("action", params["change_reference"])
        self.assertEqual(params["preview_no_value"].get("action"), "store_true")
        self.assertEqual(params["deprecated_no_value"].get("action"), "store_true")
        self.assertEqual(params["store_false_nargs_0"].get("action"), "store_false")
        for para in params.values():
            self.assertNotIn("nargs", para)

    def test_options_that_take_a_value_have_no_action(self):
        def register(c):
            c.argument("plain")
            c.argument("store", action="store")
            c.argument("append", action="append")
            c.argument("optional_value", action=_OptionalValueAction, nargs="?")
            c.argument("preview_value", is_preview=True)
            c.argument("preview_append", action="append", is_preview=True)
            c.argument("deprecated_optional_value", action=_OptionalValueAction, nargs="?",
                       deprecate_info=c.deprecate(hide=False))

        params = _params(self._register(register))
        self.assertEqual(len(params), 7)
        for name, para in params.items():
            self.assertNotIn("action", para, name)

    def test_ignored_argument_is_skipped(self):
        def register(c):
            c.ignore("cmd")
            c.argument("flag", action="store_true")

        params = _params(self._register(register))
        self.assertEqual(sorted(params), ["flag"])


if __name__ == '__main__':
    unittest.main()
