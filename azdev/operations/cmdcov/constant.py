# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

ENCODING = 'utf-8'

# https://github.com/Azure/azure-cli/blob/dev/.github/CODEOWNERS
CLI_OWN_MODULES = ['cloud', 'container', 'databoxedge', 'keyvault', 'monitor', 'network',
                   'privatedns', 'profile', 'resource', 'role', 'storage', 'vm']

EXCLUDE_MODULES = ['extension', 'feedback', 'util']

GLOBAL_EXCLUDE_COMMANDS = ['wait']

EXCLUDE_COMMANDS = {
    'network': [
        # No bastion to test
        'network bastion rdp',
        'network bastion ssh',
        'network bastion tunnel',
        # No dns to test
        'network dns record-set a list',
        'network dns record-set aaaa delete',
        'network dns record-set aaaa list',
        'network dns record-set aaaa show',
        'network dns record-set aaaa update',
        'network dns record-set caa delete',
        'network dns record-set caa list',
        'network dns record-set caa show',
        'network dns record-set caa update',
        'network dns record-set cname list',
        'network dns record-set cname show',
        'network dns record-set mx delete',
        'network dns record-set mx list',
        'network dns record-set mx show',
        'network dns record-set mx update',
        'network dns record-set ns delete',
        'network dns record-set ns list',
        'network dns record-set ns update',
        'network dns record-set ptr delete',
        'network dns record-set ptr list',
        'network dns record-set ptr show',
        'network dns record-set ptr update',
        'network dns record-set soa show',
        'network dns record-set srv delete',
        'network dns record-set srv list',
        'network dns record-set srv show',
        'network dns record-set srv update',
        'network dns record-set txt delete',
        'network dns record-set txt show',
        'network dns record-set txt update'
    ]
}


GLOBAL_PARAMETERS = [
    ['--debug'],
    ['--help', '-h'],
    ['--only-show-errors'],
    ['--output', '-o'],
    ['--query'],
    ['--query-examples'],
    ['--subscription'],
    ['--verbose'],
]
GENERIC_UPDATE_PARAMETERS = [
    ['--add'],
    ['--force-string'],
    ['--remove'],
    ['--set'],
]
WAIT_CONDITION_PARAMETERS = [
    ['--created'],
    ['--custom'],
    ['--deleted'],
    ['--exists'],
    ['--interval'],
    ['--timeout'],
    ['--updated'],
]
OTHER_PARAMETERS = [
    # batch
    ['--account-name'], ['--account-key'], ['--account-endpoint'],
    ['--ids'],
    ['--ignore-errors'],
    ['--location', '-l'],
    ['--username', '-u'],
    ['--password', '-p'],
    ['--name', '-n'],
    ['--no-wait'],
    ['--resource-group', '-g'],
    ['--tags'],
    ['--yes', '-y'],
]

CMD_PATTERN = [
    # self.cmd( # test.cmd(
    r'.\w{0,}cmd\(\n',
    # self.cmd('xxxx or self.cmd("xxx or test.cmd(' or fstring
    r'.\w{0,}cmd\(f?(?:\'|")(.*)(?:\'|")',
    # xxxcmd = '' or xxxcmd = "" or xxxcmd1 or ***Command or ***command or fstring
    r'(?:cmd|command|Command)\d* = f?(?:\'|"){1}([a-z]+.*)(?:\'|"){1}',
    # r'self.cmd\(\n', r'cmd = (?:\'|")(.*)(?:\'|")(.*)?',
    # xxxcmd = """ or xxxcmd = ''' or xxxcmd1
    r'cmd\d* = (?:"{3}|\'{3})(.*)',
]
QUO_PATTERN = r'(["\'])((?:\\\1|(?:(?!\1)).)*)(\1)'
END_PATTERN = r'(\)|checks=|,\n)'
DOCS_END_PATTERN = r'"{3}$|\'{3}$'
NOT_END_PATTERN = r'^(\s)+(\'|")'

RED = 'red'
ORANGE = 'orange'
GREEN = 'green'
BLUE = 'blue'
GOLD = 'gold'

RED_PCT = 30
ORANGE_PCT = 60
GREEN_PCT = 80
BLUE_PCT = 99
