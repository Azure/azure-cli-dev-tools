ENCODING = 'utf-8'
EXCLUDE_COMMANDS = ['wait']

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

# storage
# 'cloud show --query profile -otsv'
# 'storage account keys list -n {} -g {} --query "key1" -otsv'
# 'storage account keys list -n {} -g {} --query "[0].value" -otsv'
# 'storage account show-connection-string -n {} -g {} --query connectionString -otsv'
# 'storage account show -n {} -g {} --query id -otsv'
# ' --auth-mode login'
# '{} --account-name {} --account-key {}'
# '{} --account-name {} --account-key {}'
# 'storage container create -n {}'
# 'storage share create -n {}'
# 'storage fs create -n {}'


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


EXCLUDE_MOD = ['acs', 'apim', 'aro', 'batch', 'billing', 'cdn', 'cloud', 'dla', 'extension', 'hdinsight', 'lab',
               'marketplaceordering', 'profile', 'rdbms', 'relay', 'servicebus', 'storage']
OWN_MOD = ['vm', 'network', 'storage']

RED = 'red'
ORANGE = 'orange'
GREEN = 'green'
BLUE = 'blue'
GOLD = 'gold'

RED_PCT = 30
ORANGE_PCT = 60
GREEN_PCT = 80
BLUE_PCT = 99

# https://github.com/Azure/azure-cli/blob/dev/.github/CODEOWNERS
CLI_OWN_MODULES = ['cloud', 'container', 'databoxedge', 'keyvault', 'monitor', 'network',
                   'privatedns', 'profile', 'resource', 'role', 'storage', 'vm']

EXCLUDE_MODULES = ['extension', 'feedback', 'util']