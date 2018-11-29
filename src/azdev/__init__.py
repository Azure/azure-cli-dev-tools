# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from __future__ import print_function
import sys

from knack import CLI, CLICommandsLoader

from azdev.help import helps
from azdev.utilities import get_azdev_config_dir


__VERSION__ = "0.1.0"


class AzDevCli(CLI):

    def get_cli_version(self):
        return __VERSION__


class AzDevCommandsLoader(CLICommandsLoader):
    def load_command_table(self, args):
        from azdev.commands import load_command_table

        load_command_table(self, args)
        return super(AzDevCommandsLoader, self).load_command_table(args)

    def load_arguments(self, command):
        from azdev.params import load_arguments

        load_arguments(self, command)
        super(AzDevCommandsLoader, self).load_arguments(command)


azdev = AzDevCli(cli_name='azdev', commands_loader_cls=AzDevCommandsLoader,
                 config_dir=get_azdev_config_dir())
exit_code = azdev.invoke(sys.argv[1:])
sys.exit(exit_code)
