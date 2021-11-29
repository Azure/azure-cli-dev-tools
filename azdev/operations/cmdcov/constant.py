ENCODING = 'utf-8'
GLOBAL_PARAMETERS = ['--debug', '--help', '-h', '--only-show-errors', '--output', '-o', '--query', '--query-examples',
                        '--subscription', '--verbose']
GENERIC_UPDATE_PARAMETERS = ['--add', '--force-string', '--remove', '--set']
WAIT_CONDITION_PARAMETERS = ['--created', '--custom', '--deleted', '--exists', '--interval', '--timeout', '--updated']
OTHER_PARAMETERS = [
        '--admin-username', '--admin-password',
        '--capacity-reservation-group', '--capacity-reservation-name',
        '--ids', '--ignore-errors',
        '--location', '-l',
        '--name', '-n', '--no-wait',
        '--username', '-u',
        '--password', '-p',
        '--resource-group', '-g',
        '--tags',
        '--windows-admin-username', '--windows-admin-password',
        '--yes', '-y',
    ]

CMD_PATTERN = r'self.cmd\((?:\'|")(.*)(?:\'|")(.*)?\n'
QUO_PATTERN = r'(["\'])((?:\\\1|(?:(?!\1)).)*)(\1)'
END_PATTERN = r'(\)|checks=|,\n)'

EXCLUDE_MOD = ['acs', 'apim', 'aro', 'batch', 'billing', 'cdn', 'cloud', 'dla', 'extension', 'hdinsight', 'lab',
               'marketplaceordering', 'profile', 'rdbms', 'relay', 'servicebus', 'storage']
OWN_MOD = ['vm', 'network', 'storage']

RED = 'red'
ORANGE = 'orange'
GREEN = 'green'
BLUE = 'blue'
GOLD = 'gold'

RED_PCT = '30%'
ORANGE_PCT = '60%'
GREEN_PCT = '80%'
BLUE_PCT = '99%'

