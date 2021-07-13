# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import sys

from knack import CLI, CLICommandsLoader

from azdev.help import helps  # pylint: disable=unused-import
from azdev.utilities import get_azdev_config_dir


class AzDevCli(CLI):

    def get_cli_version(self):
        from azdev import __VERSION__
        return __VERSION__


class AzDevCommandsLoader(CLICommandsLoader):
    def load_command_table(self, args):
        from azdev.commands import load_command_table

        load_command_table(self, args)
        return super().load_command_table(args)

    def load_arguments(self, command):
        from azdev.params import load_arguments

        load_arguments(self, command)
        super().load_arguments(command)


def main():
    try:
        azdev = AzDevCli(cli_name='azdev', commands_loader_cls=AzDevCommandsLoader,
                         config_dir=get_azdev_config_dir())
        exit_code = azdev.invoke(sys.argv[1:])
        sys.exit(exit_code)
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == "__main__":
    main()
