# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import shutil
import sys
import time
import requests
import yaml

from jinja2 import FileSystemLoader, Environment
from knack.log import get_logger
from tqdm import tqdm
from azdev.operations.regex import get_all_tested_commands_from_regex
from azdev.utilities.path import get_azdev_repo_path, get_cli_repo_path, find_files

logger = get_logger(__name__)

try:
    with open(os.path.join(get_cli_repo_path(), 'scripts', 'ci', 'cmdcov.yml'), 'r') as file:
        config = yaml.safe_load(file)
# pylint: disable=broad-exception-caught
except Exception:
    url = "https://raw.githubusercontent.com/Azure/azure-cli/dev/scripts/ci/cmdcov.yml"
    response = requests.get(url)
    config = yaml.safe_load(response.text)
ENCODING = config['ENCODING']
GLOBAL_PARAMETERS = config['GLOBAL_PARAMETERS']
GENERIC_UPDATE_PARAMETERS = config['GENERIC_UPDATE_PARAMETERS']
WAIT_CONDITION_PARAMETERS = config['WAIT_CONDITION_PARAMETERS']
OTHER_PARAMETERS = config['OTHER_PARAMETERS']
RED = config['RED']
ORANGE = config['ORANGE']
GREEN = config['GREEN']
BLUE = config['BLUE']
GOLD = config['GOLD']
RED_PCT = config['RED_PCT']
ORANGE_PCT = config['ORANGE_PCT']
GREEN_PCT = config['GREEN_PCT']
BLUE_PCT = config['BLUE_PCT']
CLI_OWN_MODULES = config['CLI_OWN_MODULES']
EXCLUDE_COMMANDS = config['EXCLUDE_COMMANDS']
GLOBAL_EXCLUDE_COMMANDS = config['GLOBAL_EXCLUDE_COMMANDS']


# pylint: disable=too-many-instance-attributes
class CmdcovManager:

    def __init__(self, selected_mod_names=None, selected_mod_paths=None, loaded_help=None, level=None,
                 enable_cli_own=None, exclusions=None):
        self.selected_mod_names = selected_mod_names
        self.selected_mod_paths = selected_mod_paths
        self.loaded_help = loaded_help
        self.level = level
        self.enable_cli_own = enable_cli_own
        self.all_commands = {m: [] for m in self.selected_mod_names}
        self.all_tested_commands = {m: [] for m in self.selected_mod_names}
        self.all_live_commands = []
        self.all_untested_commands = {}
        self.command_test_coverage = {'Total': [0, 0, 0]}
        self.date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.report_date = '-'.join(self.date.replace(':', '-').split())
        self.cmdcov_path = os.path.dirname(__file__)
        self.exclusions = exclusions
        self.width = 60
        self.fillchar = '-'

    def run(self):
        self._get_all_commands()
        self._get_all_tested_commands_from_regex()
        self._get_all_tested_commands_from_record()
        self._run_command_test_coverage()
        self._get_all_tested_commands_from_live()
        self._run_command_test_coverage_enhance()
        html_file = self._render_html()
        if self.enable_cli_own:
            command_test_coverage = {k: v for k, v in self.command_test_coverage.items() if k in CLI_OWN_MODULES}
            total_tested = 0
            total_untested = 0
            command_test_coverage['Total'] = [0, 0, 0]
            for module in command_test_coverage.keys():
                total_tested += command_test_coverage[module][0] if command_test_coverage[module] else 0
                total_untested += command_test_coverage[module][1] if command_test_coverage[module] else 0
            command_test_coverage['Total'][0] = total_tested
            command_test_coverage['Total'][1] = total_untested
            command_test_coverage['Total'][2] = f'{total_tested / (total_tested + total_untested):.3%}'
            self._render_cli_html(command_test_coverage)
        self._browse(html_file)

    def _get_all_commands(self):
        """
        GLOBAL_EXCLUDE_COMMANDS: List[str]
        EXCLUDE_COMMANDS: Dict[str: List[str]]
        exclusions_comands: List[str]
        exclude_parameters: List[List[str]]
        exclusions_parameters: List[Tuple[str, str]]
        get all commands from loaded_help
        """
        exclude_parameters = []
        exclude_parameters += GLOBAL_PARAMETERS + GENERIC_UPDATE_PARAMETERS + WAIT_CONDITION_PARAMETERS + \
            OTHER_PARAMETERS
        exclude_parameters = [sorted(i) for i in exclude_parameters]

        # some module like vm have multiple command like vm vmss disk snapshot ...
        # pylint: disable=too-many-nested-blocks, too-many-boolean-expressions
        exclusions_comands = []
        exclusions_parameters = []
        for c, v in self.exclusions.items():
            if 'parameters' in v:
                for p, r in v['parameters'].items():
                    if 'missing_parameter_test_coverage' in r['rule_exclusions']:
                        exclusions_parameters.append((c, p))
            elif 'rule_exclusions' in v:
                if 'missing_command_test_coverage' in v['rule_exclusions']:
                    exclusions_comands.append(c)
        print("\033[31m" + "Get all commands".center(self.width, self.fillchar) + "\033[0m")
        time.sleep(0.1)
        for _, y in tqdm(self.loaded_help.items()):
            if hasattr(y, 'command_source') and y.command_source in self.selected_mod_names:
                module = y.command_source
            elif hasattr(y, 'command_source') and hasattr(y.command_source, 'extension_name'):
                module = 'azext_' + y.command_source.extension_name.replace('-', '_')
                if module not in self.selected_mod_names:
                    module = None
            else:
                continue
            if (not y.deprecate_info) and module:
                if y.command.split()[-1] not in GLOBAL_EXCLUDE_COMMANDS and \
                        y.command not in EXCLUDE_COMMANDS.get(module, []) and \
                        y.command not in exclusions_comands:
                    if self.level == 'argument':
                        for parameter in y.parameters:
                            # TODO support linter_exclusions.yml
                            if sorted(parameter.name_source) not in exclude_parameters:
                                opt_list = [opt for opt in parameter.name_source if opt.startswith('-')]
                                if opt_list:
                                    self.all_commands[module].append(f'{y.command} {opt_list}')
                    else:
                        self.all_commands[module].append(f'{y.command}')

    def _get_all_tested_commands_from_regex(self):
        """
        get all tested commands from test_*.py
        """
        # pylint: disable=too-many-nested-blocks
        print("\033[31m" + "Get tested commands from regex".center(self.width, self.fillchar) + "\033[0m")
        time.sleep(0.1)
        for idx, path in enumerate(tqdm(self.selected_mod_paths)):
            if 'azure-cli-extensions' in path:
                for dirname in os.listdir(path):
                    if dirname.startswith('azext'):
                        test_dir = os.path.join(path, dirname, 'tests')
                        break
            else:
                test_dir = os.path.join(path, 'tests')
            files = find_files(test_dir, '*.py')
            for f in files:
                with open(os.path.join(test_dir, f), 'r', encoding=ENCODING) as f:
                    lines = f.readlines()
                ref = get_all_tested_commands_from_regex(lines)
                self.all_tested_commands[self.selected_mod_names[idx]] += ref

    def _get_all_tested_commands_from_record(self):
        """
        get all tested commands from recording files
        """
        print("\033[31m" + "Get tested commands from recording files".center(self.width, self.fillchar) + "\033[0m")
        time.sleep(0.1)
        for idx, path in enumerate(tqdm(self.selected_mod_paths)):
            if 'azure-cli-extensions' in path:
                for dirname in os.listdir(path):
                    if dirname.startswith('azext'):
                        test_dir = os.path.join(path, dirname, 'tests')
                        break
            else:
                test_dir = os.path.join(path, 'tests')
            files = find_files(test_dir, 'test*.yaml')
            for f in files:
                with open(os.path.join(test_dir, f)) as f:
                    # safe_load can not determine a constructor for the tag: !!python/unicode
                    records = yaml.load(f, Loader=yaml.Loader) or {}
                    for record in records['interactions']:
                        # ['acr agentpool create']
                        command = record['request']['headers'].get('CommandName', [''])[0]
                        # ['-n -r']
                        argument = record['request']['headers'].get('ParameterSetName', [''])[0]
                        if command or argument:
                            cmd = command + ' ' + argument
                            self.all_tested_commands[self.selected_mod_names[idx]].append(cmd)

    def _get_all_tested_commands_from_live(self):
        with open(os.path.join(self.cmdcov_path, 'tested_command.txt'), 'r') as f:
            self.all_live_commands = f.readlines()

    def _run_command_test_coverage(self):
        """
        all_commands: All commands that need to be test
        all_tested_commands: All commands already tested
        command_test_coverage: {{module1: pct}, {module2: pct}}
        module: vm
        pct: xx.xxx%
        """
        import ast
        for module in self.all_commands.keys():
            self.command_test_coverage[module] = []
            self.all_untested_commands[module] = []
        # pylint: disable=too-many-nested-blocks
        for module in self.all_commands.keys():
            count = 0
            for command in self.all_commands[module]:
                exist_flag = False
                prefix = command.rsplit('[', maxsplit=1)[0]
                opt_list = ast.literal_eval('[' + command.rsplit('[', maxsplit=1)[1]) if self.level == 'argument' \
                    else []
                for cmd in self.all_tested_commands[module]:
                    if prefix in cmd or \
                            module == 'rdbms' and prefix.split(maxsplit=1)[1] in cmd:
                        if self.level == 'argument':
                            for opt in opt_list:
                                if opt in cmd:
                                    count += 1
                                    exist_flag = True
                                    if exist_flag:
                                        break
                        else:
                            count += 1
                            exist_flag = True
                            if exist_flag:
                                break
                    if exist_flag:
                        break
                else:
                    self.all_untested_commands[module].append(command)
            try:
                self.command_test_coverage[module] = [count, len(self.all_untested_commands[module]),
                                                      f'{count / len(self.all_commands[module]):.3%}']
            except ZeroDivisionError:
                self.command_test_coverage[module] = [0, 0, 'N/A']
            self.command_test_coverage['Total'][0] += count
            self.command_test_coverage['Total'][1] += len(self.all_untested_commands[module])
        self.command_test_coverage['Total'][2] = f'''{self.command_test_coverage["Total"][0] /
                                                 (self.command_test_coverage["Total"][0] +
                                                  self.command_test_coverage["Total"][1]):.3%}'''
        logger.warning(self.command_test_coverage)
        return self.command_test_coverage

    def _run_command_test_coverage_enhance(self):
        """
        all_untest_commands: {[module]:[],}
        all_tested_commands_from_file: []
        command_test_coverage: {[module: [test, untested, pct]
        module: vm
        percentage: xx.xxx%
        """
        import ast
        total_tested = 0
        total_untested = 0
        # pylint: disable=too-many-nested-blocks
        for module, untested_commands in self.all_untested_commands.items():
            for cmd_idx, command in enumerate(untested_commands):
                exist_flag = False
                prefix = command.rsplit('[', maxsplit=1)[0]
                opt_list = ast.literal_eval('[' + command.rsplit('[', maxsplit=1)[1]) if self.level == 'argument' \
                    else []
                for cmd in self.all_live_commands:
                    if prefix in cmd:
                        if self.level == 'argument':
                            for opt in opt_list:
                                if opt in cmd:
                                    self.command_test_coverage[module][0] += 1
                                    untested_commands.pop(cmd_idx)
                                    exist_flag = True
                                    if exist_flag:
                                        break
                        else:
                            self.command_test_coverage[module][0] += 1
                            untested_commands.pop(cmd_idx)
                            exist_flag = True
                            if exist_flag:
                                break
                    if exist_flag:
                        break
            try:
                self.command_test_coverage[module][1] = len(untested_commands)
                self.command_test_coverage[module][2] = f'''{self.command_test_coverage[module][0] /
                                                        (self.command_test_coverage[module][0] +
                                                         self.command_test_coverage[module][1]):.3%}'''
            except ZeroDivisionError:
                self.command_test_coverage[module] = [0, 0, 'N/A']
            total_tested += self.command_test_coverage[module][0] if self.command_test_coverage[module] else 0
            total_untested += self.command_test_coverage[module][1] if self.command_test_coverage[module] else 0
        self.command_test_coverage['Total'][0] = total_tested
        self.command_test_coverage['Total'][1] = total_untested
        self.command_test_coverage['Total'][2] = f'{total_tested / (total_tested + total_untested):.3%}'
        logger.warning(self.command_test_coverage)

    def _render_html(self):
        """
        :return: Return a HTML string
        """
        html_path = self.get_html_path()
        description = 'Command' if self.level == 'command' else 'Command Argument'
        j2_loader = FileSystemLoader(self.cmdcov_path)
        env = Environment(loader=j2_loader)
        j2_tmpl = env.get_template('./index.j2')
        for item in self.command_test_coverage.values():
            color, percentage = self._get_color(item)
            item.append({'color': color, 'percentage': percentage})
        total = self.command_test_coverage.pop('Total')

        content = j2_tmpl.render(description=description,
                                 enable_cli_own=self.enable_cli_own,
                                 date=self.date,
                                 Total=total,
                                 command_test_coverage=self.command_test_coverage)
        index_html = os.path.join(html_path, 'index.html')
        with open(index_html, 'w', encoding=ENCODING) as f:
            f.write(content)

        # render child html
        print("\033[31m" + "Render test coverage report".center(self.width, self.fillchar) + "\033[0m")
        time.sleep(0.1)
        for module, coverage in tqdm(self.command_test_coverage.items()):
            if coverage:
                self._render_child_html(module, coverage, self.all_untested_commands[module])

        # copy source
        css_source = os.path.join(self.cmdcov_path, 'component.css')
        ico_source = os.path.join(self.cmdcov_path, 'favicon.ico')
        js_source = os.path.join(self.cmdcov_path, 'component.js')
        try:
            shutil.copy(css_source, html_path)
            shutil.copy(ico_source, html_path)
            shutil.copy(js_source, html_path)
        except IOError as e:
            logger.error("Unable to copy file %s", e)
        except Exception:  # pylint: disable=broad-except
            logger.error("Unexpected error: %s", sys.exc_info())

        return index_html

    def _render_cli_html(self, command_test_coverage):
        """
        render cli own html string
        """
        html_path = self.get_html_path()
        description = 'Command' if self.level == 'command' else 'Command Argument'
        j2_loader = FileSystemLoader(self.cmdcov_path)
        env = Environment(loader=j2_loader)
        j2_tmpl = env.get_template('./index2.j2')
        for module, item in command_test_coverage.items():
            color, percentage = self._get_color(item)
            command_test_coverage[module].append({'color': color, 'percentage': percentage})
        total = command_test_coverage.pop('Total')

        content = j2_tmpl.render(description=description,
                                 date=self.date,
                                 Total=total,
                                 command_test_coverage=command_test_coverage)
        index_html = os.path.join(html_path, 'index2.html')
        with open(index_html, 'w', encoding=ENCODING) as f:
            f.write(content)

    def _render_child_html(self, module, coverage, untested_commands):
        """
        render every module html
        """
        html_path = self.get_html_path()
        j2_loader = FileSystemLoader(self.cmdcov_path)
        env = Environment(loader=j2_loader)
        j2_tmpl = env.get_template('./module.j2')
        content = j2_tmpl.render(module=module,
                                 enable_cli_own=self.enable_cli_own,
                                 date=self.date,
                                 coverage=coverage,
                                 untested_commands=untested_commands)
        with open(f'{html_path}/{module}.html', 'w', encoding=ENCODING) as f:
            f.write(content)

    @staticmethod
    def _get_color(coverage):
        """
        :param coverage:
        :return: color and percentage
        """

        percentage = int(round(float(coverage[2][:-1]), 0)) if coverage[2] != 'N/A' else coverage[2]
        if percentage == 'N/A':
            color = 'N/A'
        elif percentage < RED_PCT:
            color = RED
        elif percentage < ORANGE_PCT:
            color = ORANGE
        elif percentage < GREEN_PCT:
            color = GREEN
        elif percentage < BLUE_PCT:
            color = BLUE
        else:
            color = GOLD

        return color, percentage

    def get_html_path(self):
        """
        :return: html_path
        """
        root_path = get_azdev_repo_path()
        html_path = os.path.join(root_path, 'cmd_coverage', self.level, f'{self.report_date}')
        if not os.path.exists(html_path):
            os.makedirs(html_path)
        return html_path

    @staticmethod
    def get_container_name():
        """
        Generate container name in storage account. It is also an identifier of the pipeline run.
        :return:
        """
        import datetime
        import random
        import string
        logger.warning('Enter get_container_name()')
        container_time = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        random_id = ''.join(random.choice(string.digits) for _ in range(6))
        name = container_time + '-' + random_id
        logger.warning('Exit get_container_name()')
        return name

    @staticmethod
    def upload_files(container, html_path, account_key):
        """
        Upload html and json files to container
        """
        logger.warning('Enter upload_files()')

        # Create container
        cmd = 'az storage container create -n {} --account-name clitestresultstac --account-key {}' \
              ' --public-access container'.format(container, account_key)
        os.system(cmd)

        # Upload files
        for root, dirs, files in os.walk(html_path):
            logger.debug(dirs)
            for name in files:
                if name.endswith('html') or name.endswith('css'):
                    fullpath = os.path.join(root, name)
                    cmd = 'az storage blob upload -f {} -c {} -n {} --account-name clitestresultstac'
                    cmd = cmd.format(fullpath, container, name)
                    logger.warning('Running: %s', cmd)
                    os.system(cmd)

        logger.warning('Exit upload_files()')

    @staticmethod
    def _browse(uri, browser_name=None):  # throws ImportError, webbrowser.Error
        """Browse uri with named browser. Default browser is customizable by $BROWSER"""

        def is_wsl():
            # "Official" way of detecting WSL: https://github.com/Microsoft/WSL/issues/423#issuecomment-221627364
            # Run `uname -a` to get 'release' without python
            #   - WSL 1: '4.4.0-19041-Microsoft'
            #   - WSL 2: '4.19.128-microsoft-standard'
            import platform
            uname = platform.uname()
            platform_name = getattr(uname, 'system', uname[0]).lower()
            release = getattr(uname, 'release', uname[2]).lower()
            return platform_name == 'linux' and 'microsoft' in release

        import webbrowser  # Lazy import. Some distro may not have this.
        if browser_name:
            browser_opened = webbrowser.get(browser_name).open(uri)
        else:
            # This one can survive BROWSER=nonexist, while get(None).open(...) can not
            browser_opened = webbrowser.open(uri)
        logger.warning(uri)

        # In WSL which doesn't have www-browser, try launching browser with PowerShell
        if not browser_opened and is_wsl():
            try:
                import subprocess
                # https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_powershell_exe
                # Ampersand (&) should be quoted
                exit_code = subprocess.call(
                    ['powershell.exe', '-NoProfile', '-Command', 'Start-Process "{}"'.format(uri)])
                browser_opened = exit_code == 0
            except FileNotFoundError:  # WSL might be too old
                pass
        return browser_opened
