# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os
import time
import yaml
import shutil
import sys

from knack.help_files import helps
from knack.log import get_logger
from knack.util import CLIError

from azdev.utilities import (
    heading, subheading, display, get_path_table, require_azure_cli, filter_by_git_diff)
from azdev.utilities.path import get_cli_repo_path, get_ext_repo_paths, get_azdev_repo_path, find_files
from .util import filter_modules, merge_exclusion
from .constant import (
    ENCODING, GLOBAL_PARAMETERS, GENERIC_UPDATE_PARAMETERS, WAIT_CONDITION_PARAMETERS, OTHER_PARAMETERS,
    CMD_PATTERN, QUO_PATTERN, END_PATTERN, DOCS_END_PATTERN, NOT_END_PATTERN, EXCLUDE_MOD, RED, ORANGE, GREEN,
    BLUE, GOLD, RED_PCT, ORANGE_PCT, GREEN_PCT, BLUE_PCT, CLI_OWN_MODULES, EXCLUDE_MODULES)


logger = get_logger(__name__)


# pylint:disable=too-many-locals, too-many-statements, too-many-branches
def run_cmdcov(modules=None, git_source=None, git_target=None, git_repo=None, level='command'):
    """
    :param modules:
    :param git_source:
    :param git_target:
    :param git_target:
    :return: None
    """
    require_azure_cli()
    from azure.cli.core import get_default_cli  # pylint: disable=import-error
    from azure.cli.core.file_util import (  # pylint: disable=import-error
        get_all_help, create_invoker_and_load_cmds_and_args)

    heading('CLI Command Coverage')

    # allow user to run only on CLI or extensions
    cli_only = modules == ['CLI']
    # ext_only = modules == ['EXT']
    enable_cli_own = True if cli_only or modules is None else False
    if cli_only:
        modules = None
    # if cli_only or ext_only:
    #     modules = None

    selected_modules = get_path_table(include_only=modules)

    # filter down to only modules that have changed based on git diff
    selected_modules = filter_by_git_diff(selected_modules, git_source, git_target, git_repo)

    if not any(selected_modules.values()):
        logger.warning('No commands selected to check.')

    for module in EXCLUDE_MODULES:
        selected_modules['mod'] = {k:v for k,v in selected_modules['mod'].items() if k not in EXCLUDE_MODULES}
        selected_modules['ext'] = {k:v for k,v in selected_modules['ext'].items() if k not in EXCLUDE_MODULES}

    if cli_only:
        selected_mod_names = list(selected_modules['mod'].keys())
        selected_mod_paths = list(selected_modules['mod'].values())
    # elif ext_only:
    #     selected_mod_names = list(selected_modules['ext'].keys())
    #     selected_mod_paths = list(selected_modules['ext'].values())
    else:
        selected_mod_names = list(selected_modules['mod'].keys())
        selected_mod_paths = list(selected_modules['mod'].values())

    if selected_mod_names:
        display('Modules: {}\n'.format(', '.join(selected_mod_names)))

    start = time.time()
    display('Initializing cmdcov with command table and help files...')
    az_cli = get_default_cli()

    # load commands, args, and help
    create_invoker_and_load_cmds_and_args(az_cli)
    loaded_help = get_all_help(az_cli)

    stop = time.time()
    logger.info('Commands and help loaded in %i sec', stop - start)
    command_loader = az_cli.invocation.commands_loader

    # format loaded help
    loaded_help = {data.command: data for data in loaded_help if data.command}

    all_commands = _get_all_commands(selected_mod_names, loaded_help, level)
    all_tested_commands = _get_all_tested_commands(selected_mod_names, selected_mod_paths)
    command_coverage, all_untested_commands = _run_commands_coverage(all_commands, all_tested_commands, level)
    all_tested_cmd_from_file = _get_all_tested_commands_from_file()
    command_coverage, all_untested_commands = _run_commands_coverage_enhance(all_untested_commands, all_tested_cmd_from_file, command_coverage, level)
    html_file, date = _render_html(command_coverage, all_untested_commands, level, enable_cli_own)
    if enable_cli_own:
        command_coverage = {k:v for k,v in command_coverage.items() if k in CLI_OWN_MODULES}
        all_untested_commands = {k:v for k,v in all_untested_commands.items() if k in CLI_OWN_MODULES}
        total_tested = 0
        total_untested = 0
        command_coverage['Total'] = [0, 0, 0]
        for module in command_coverage.keys():
            total_tested += command_coverage[module][0] if command_coverage[module] else 0
            total_untested += command_coverage[module][1] if command_coverage[module] else 0
        command_coverage['Total'][0] = total_tested
        command_coverage['Total'][1] = total_untested
        command_coverage['Total'][2] = f'{total_tested / (total_tested + total_untested):.3%}'
        _render_cli_html(command_coverage, all_untested_commands, level, date)
    subheading('Results')
    _browse(html_file)


def _browse(uri, browser_name=None):  # throws ImportError, webbrowser.Error
    """Browse uri with named browser. Default browser is customizable by $BROWSER"""
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


def _get_all_commands(selected_mod_names, loaded_help, level):
    """
    :param selected_mod_names:
    :param loaded_help:
    :return: all_test_commands
    """
    # selected_mod_names = ['vm']
    exclude_parameters = []
    exclude_parameters += GLOBAL_PARAMETERS + GENERIC_UPDATE_PARAMETERS + GENERIC_UPDATE_PARAMETERS + OTHER_PARAMETERS
    [i.sort() for i in exclude_parameters]

    all_test_commands = {m: [] for m in selected_mod_names}
    # like module vm have multiple command like vm vmss disk snapshot
    for _, y in loaded_help.items():
        if hasattr(y, 'command_source') and y.command_source in selected_mod_names or \
           hasattr(y, 'command_source') and hasattr(y.command_source, 'extension_name') and y.command_source.extension_name in selected_mod_names:
            module = y.command_source.extension_name if hasattr(y.command_source, 'extension_name') else y.command_source
            if level == 'argument':
                for parameter in y.parameters:
                    opt_list = []
                    parameter.name_source.sort()
                    if parameter.name_source not in exclude_parameters:
                        for opt in parameter.name_source:
                            if opt.startswith('-'):
                                opt_list.append(opt)
                    if opt_list:
                        all_test_commands[module].append(f'{y.command} {opt_list}')
            else:
                all_test_commands[module].append(f'{y.command}')

    return all_test_commands


def _get_all_tested_commands(selected_mod_names, selected_mod_path):
    """
    :param selected_mod_names:
    :param selected_mod_path:
    :return: all_tested_commands
    """
    import re
    all_tested_commands = {m: [] for m in selected_mod_names}
    for idx, path in enumerate(selected_mod_path):
        test_dir = os.path.join(path, 'tests')
        files = find_files(test_dir, '*.py')
        for f in files:
            with open(os.path.join(test_dir, f), 'r', encoding='utf-8') as f:
                try:
                    lines = f.readlines()
                except Exception as e:
                    print('readlines error', e, f)
                # test_image_builder_commands.py 44
                total_lines = len(lines)
                row_num = 0
                count = 1
                while row_num < total_lines:
                    cmd_idx = None
                    if re.findall(CMD_PATTERN[0], lines[row_num]):
                        cmd_idx = 0
                    if cmd_idx is None and re.findall(CMD_PATTERN[1], lines[row_num]):
                        cmd_idx = 1
                    if cmd_idx is None and re.findall(CMD_PATTERN[2], lines[row_num]):
                        cmd_idx = 2
                    if cmd_idx is None and re.findall(CMD_PATTERN[3], lines[row_num]):
                        cmd_idx = 3
                    if cmd_idx is not None:
                        command = re.findall(CMD_PATTERN[cmd_idx], lines[row_num])[0]
                        while row_num < total_lines:
                            if (cmd_idx in [0, 1] and not re.findall(END_PATTERN, lines[row_num])) or \
                               (cmd_idx == 2 and (row_num + 1) < total_lines and re.findall(NOT_END_PATTERN, lines[row_num + 1])):
                                row_num += 1
                                try:
                                    command += re.findall(QUO_PATTERN, lines[row_num])[0][1]
                                except Exception as e:
                                    # pass
                                    print('Exception1', row_num, selected_mod_names[idx], f)
                            elif cmd_idx == 3 and (row_num + 1) < total_lines and not re.findall(DOCS_END_PATTERN, lines[row_num]):
                                row_num += 1
                                command += lines[row_num][:-1]
                            else:
                                command = command + ' ' + str(count)
                                all_tested_commands[selected_mod_names[idx]].append(command)
                                row_num += 1
                                count += 1
                                break
                        else:
                            command = command + ' ' + str(count)
                            all_tested_commands[selected_mod_names[idx]].append(command)
                            row_num += 1
                            count += 1
                            break
                    else:
                        row_num += 1
    return all_tested_commands


def _get_all_tested_commands_from_file():
    with open(os.path.join(get_azdev_repo_path(), 'azdev', 'operations', 'cmdcov', 'tested_command.txt'), 'r') as f:
        lines = f.readlines()
    return lines


def _run_commands_coverage(all_commands, all_tested_commands, level):
    """
    :param all_commands: All commands that need to be test
    :param all_tested_commands: All commands already tested
    :return: command_coverage and all_untested_commands
    module: vm
    percentage: xx.xxx%
    """
    import ast
    command_coverage = {'Total': [0, 0, 0]}
    all_untested_commands = {}
    for module in all_commands.keys():
        command_coverage[module] = []
        all_untested_commands[module] = []
    for module in all_commands.keys():
        count = 0
        for command in all_commands[module]:
            exist_flag = False
            prefix = command.rsplit('[', maxsplit=1)[0]
            opt_list = ast.literal_eval('[' + command.rsplit('[', maxsplit=1)[1]) if level == 'argument' else []
            for cmd in all_tested_commands[module]:
                if prefix in cmd or \
                        module == 'rdbms' and prefix.split(maxsplit=1)[1] in cmd:
                    if level == 'argument':
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
                all_untested_commands[module].append(command)
        try:
            command_coverage[module] = [count, len(all_untested_commands[module]), f'{count / len(all_commands[module]):.3%}']
        except ZeroDivisionError:
            command_coverage[module] = [0, 0, 'N/A']
        command_coverage['Total'][0] += count
        command_coverage['Total'][1] += len(all_untested_commands[module])
    command_coverage['Total'][2] = f'{command_coverage["Total"][0] / (command_coverage["Total"][0] + command_coverage["Total"][1]):.3%}'
    logger.warning(command_coverage)
    return command_coverage, all_untested_commands


def _run_commands_coverage_enhance(all_untested_commands, all_tested_commands_from_file, command_coverage, level):
    """
    :param all_untest_commands: {[module]:[],}
    :param all_tested_commands_from_file: []
    :param command_coverage: {[module: [test, untested, pct]
    :return: command_coverage and all_untested_commands
    module: vm
    percentage: xx.xxx%
    """
    import ast
    total_tested = 0
    total_untested = 0
    for module in all_untested_commands.keys():
        for cmd_idx, command in enumerate(all_untested_commands[module]):
            exist_flag = False
            prefix = command.rsplit('[', maxsplit=1)[0]
            opt_list = ast.literal_eval('[' + command.rsplit('[', maxsplit=1)[1]) if level == 'argument' else []
            for cmd in all_tested_commands_from_file:
                if prefix in cmd:
                    if level == 'argument':
                        for opt in opt_list:
                            if opt in cmd:
                                command_coverage[module][0] += 1
                                all_untested_commands[module].pop(cmd_idx)
                                exist_flag = True
                                if exist_flag:
                                    break
                    else:
                        command_coverage[module][0] += 1
                        all_untested_commands[module].pop(cmd_idx)
                        exist_flag = True
                        if exist_flag:
                            break
                if exist_flag:
                    break
        try:
            command_coverage[module][1] = len(all_untested_commands[module])
            command_coverage[module][2] = f'{command_coverage[module][0] / (command_coverage[module][0] + command_coverage[module][1]):.3%}'
        except ZeroDivisionError:
            command_coverage[module] = [0, 0, 'N/A']
        total_tested += command_coverage[module][0] if command_coverage[module] else 0
        total_untested += command_coverage[module][1] if command_coverage[module] else 0
    command_coverage['Total'][0] = total_tested
    command_coverage['Total'][1] = total_untested
    command_coverage['Total'][2] = f'{total_tested / (total_tested + total_untested):.3%}'
    logger.warning(command_coverage)
    return command_coverage, all_untested_commands


def _render_html(command_coverage, all_untested_commands, level, enable_cli_own):
    """
    :param command_coverage:
    :param all_untested_commands:
    :return: Return a HTML string
    """
    import time
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    path_date = '-'.join(date.replace(':', '-').split())
    html_path = get_html_path(path_date, level)
    content = """
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>CLI Command Coverage</title>
        <link rel="stylesheet" type="text/css" href="component.css"/>
        <link rel="shortcut icon" href="favicon.ico">
        <script type="text/javascript" src="http://code.jquery.com/jquery-1.12.4.min.js"></script>
        <script type="text/javascript" src="./component.js"></script>
    </head>
<body>
    <div class="container">
        <header>
            <h1>CLI Command Coverage Report
                <span>This is the command coverage report of CLI. Scroll down to see the every module coverage.<br>
                Any question please contact Azure Cli Team.</span>
            </h1>
"""

    if enable_cli_own:
        content += """
            <nav class="button">
                <a class="current-page" href="index.html">ALL</a>
                <a href="index2.html">CLI OWN</a>'
            </nav>
        """
    else:
        content += """
            <nav class="button">
                <a href="index.html">ALL</a>
            </nav>
        """

    content += """
        </header>
        <div class="component">
            <h3>Date: {}</h3>
    """.format(date)

    table = """
                <table>
                    <thead>
                    <tr>
                        <th id="th0" onclick="SortTable(this)" class="as">Module</th>
                        <th id="th1" onclick="SortTable(this)" class="as">Tested</th>
                        <th id="th2" onclick="SortTable(this)" class="as">Untested</th>
                        <th id="th3" onclick="SortTable(this)" class="as">Percentage</th>
                        <th id="th4" onclick="SortTable(this)" class="as">Percentage</th>
                        <th id="th5" onclick="SortTable(this)" class="as">Reports</th>
                    </tr>
                    </thead>
    """

    table += """
                    <tbody>
                    <tr>
                        <td name="td0">Total</td>
                        <td name="td1">{}</td>
                        <td name="td2">{}</td>
                        <td name="td3">{}</td>

    """.format(command_coverage['Total'][0], command_coverage['Total'][1], command_coverage['Total'][2])

    color, percentage = _get_color(command_coverage['Total'])
    table = _render_td(table, color, percentage)

    table += """
                        <td name="td5">N/A</td>
                    </tr>
    """

    command_coverage.pop('Total')

    for module, coverage in command_coverage.items():
        # feedback: []
        # find: []
        if coverage:
            reports = '<a href="{module}.html">{module} coverage report</a> '.format(module=module)
            child_html = _render_child_html(module, coverage, all_untested_commands[module], enable_cli_own, date)
            with open(f'{html_path}/{module}.html', 'w', encoding='utf-8') as f:
                f.write(child_html)
            try:
                table += """
                  <tr>
                    <td name="td0">{}</td>
                    <td name="td1">{}</td>
                    <td name="td2">{}</td>
                    <td name="td3">{}</td>
                """.format(module, coverage[0], coverage[1], coverage[2])
            except:
                print('Exception3', module, coverage, reports)

            color, percentage = _get_color(coverage)
            table = _render_td(table, color, percentage)

            table += """
                                <td name="td5">{}</td>
                            </tr>
            """.format(reports)

    table += """
                    </tbody>
                </table>
    """
    content += table

    content += """
                <p class="contact">This is the command coverage report of CLI.<br>
                    Any question please contact Azure Cli Team.</p>
            </div>
        </div><!-- /container -->
    </body>
</html>
    """
    index_html = os.path.join(html_path, 'index.html')
    with open(index_html, 'w', encoding='utf-8') as f:
        f.write(content)

    # copy source
    css_source = os.path.join(get_azdev_repo_path(), 'azdev', 'operations', 'cmdcov', 'component.css')
    ico_source = os.path.join(get_azdev_repo_path(), 'azdev', 'operations', 'cmdcov', 'favicon.ico')
    js_source = os.path.join(get_azdev_repo_path(), 'azdev', 'operations', 'cmdcov', 'component.js')
    try:
        shutil.copy(css_source, html_path)
        shutil.copy(ico_source, html_path)
        shutil.copy(js_source, html_path)
    except IOError as e:
        logger.error("Unable to copy file %s" % e)
    except:
        logger.error("Unexpected error:", sys.exc_info())

    return index_html, date


def _render_cli_html(command_coverage, all_untested_commands, level, date, enable_cli_own=True):
    """
    :param command_coverage:
    :param all_untested_commands:
    :return: Return a HTML string
    """
    path_date = '-'.join(date.replace(':', '-').split())
    html_path = get_html_path(path_date, level)
    content = """
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>CLI Own Command Coverage</title>
        <link rel="stylesheet" type="text/css" href="component.css"/>
        <link rel="shortcut icon" href="favicon.ico">
        <script type="text/javascript" src="http://code.jquery.com/jquery-1.12.4.min.js"></script>
        <script type="text/javascript" src="./component.js"></script>
    </head>
<body>
    <div class="container">
        <header>
            <h1>CLI Own Command Coverage Report
                <span>This is the command coverage report of CLI Own. Scroll down to see the every module coverage.<br>
                Any question please contact Azure Cli Team.</span>
            </h1>
            <nav class="button">
                <a href="index.html">ALL</a>
                <a class="current-page" href="index2.html">CLI OWN</a>'
            </nav>
"""

    content += """
        </header>
        <div class="component">
            <h3>Date: {}</h3>
    """.format(date)

    table = """
                <table>
                    <thead>
                    <tr>
                        <th id="th0" onclick="SortTable(this)" class="as">Module</th>
                        <th id="th1" onclick="SortTable(this)" class="as">Tested</th>
                        <th id="th2" onclick="SortTable(this)" class="as">Untested</th>
                        <th id="th3" onclick="SortTable(this)" class="as">Percentage</th>
                        <th id="th4" onclick="SortTable(this)" class="as">Percentage</th>
                        <th id="th5" onclick="SortTable(this)" class="as">Reports</th>
                    </tr>
                    </thead>
    """

    table += """
                    <tbody>
                    <tr>
                        <td name="td0">Total</td>
                        <td name="td1">{}</td>
                        <td name="td2">{}</td>
                        <td name="td3">{}</td>

    """.format(command_coverage['Total'][0], command_coverage['Total'][1], command_coverage['Total'][2])

    color, percentage = _get_color(command_coverage['Total'])
    table = _render_td(table, color, percentage)

    table += """
                        <td name="td5">N/A</td>
                    </tr>
    """

    command_coverage.pop('Total')

    for module, coverage in command_coverage.items():
        # feedback: []
        # find: []
        if coverage:
            reports = '<a href="{module}.html">{module} coverage report</a> '.format(module=module)
            try:
                table += """
                  <tr>
                    <td name="td0">{}</td>
                    <td name="td1">{}</td>
                    <td name="td2">{}</td>
                    <td name="td3">{}</td>
                """.format(module, coverage[0], coverage[1], coverage[2])
            except:
                print('Exception3', module, coverage, reports)

            color, percentage = _get_color(coverage)
            table = _render_td(table, color, percentage)

            table += """
                                <td name="td5">{}</td>
                            </tr>
            """.format(reports)

    table += """
                    </tbody>
                </table>
    """
    content += table

    content += """
                <p class="contact">This is the command coverage report of CLI Own.<br>
                    Any question please contact Azure Cli Team.</p>
            </div>
        </div><!-- /container -->
    </body>
</html>
    """
    index_html = os.path.join(html_path, 'index2.html')
    with open(index_html, 'w', encoding='utf-8') as f:
        f.write(content)

    # copy source
    css_source = os.path.join(get_azdev_repo_path(), 'azdev', 'operations', 'cmdcov', 'component.css')
    ico_source = os.path.join(get_azdev_repo_path(), 'azdev', 'operations', 'cmdcov', 'favicon.ico')
    js_source = os.path.join(get_azdev_repo_path(), 'azdev', 'operations', 'cmdcov', 'component.js')
    try:
        shutil.copy(css_source, html_path)
        shutil.copy(ico_source, html_path)
        shutil.copy(js_source, html_path)
    except IOError as e:
        logger.error("Unable to copy file %s" % e)
    except:
        logger.error("Unexpected error:", sys.exc_info())

    return index_html, date


def _render_child_html(module, command_coverage, all_untested_commands, enable_cli_own, date):
    """
    :param module:
    :param command_coverage:
    :param all_untested_commands:
    :return: Return a HTML string
    """
    content = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{module} Coverage Detail</title>
        <link rel="stylesheet" type="text/css" href="component.css"/>
        <link rel="shortcut icon" href="favicon.ico">
    </head>
    <body>
        <div class="container">
            <header>
                <h1>{module} Command Coverage Report
                    <span>This is the command coverage report of {module}. Scroll down to see the every module coverage.<br>
                    Any question please contact Azure Cli Team.</span>
                </h1>

    """.format(module=module[0].upper()+module[1:].lower())

    if enable_cli_own:
        content += """
                <nav class="button">
                    <a class="current-page" href="index.html">ALL</a>
                    <a href="index2.html">CLI OWN</a>
                </nav>
        """
    else:
        content += """
                <nav class="button">
                    <a href="index.html">ALL</a>
                </nav>
        """

    try:
        content += """
            </header>
            <div class="component">
                <h3>Date: {}</h3>
                <h3>Tested: {}, Untested: {}, Percentage: {}</h3>
        """.format(date, command_coverage[0], command_coverage[1], command_coverage[2], module)
    except:
        print('Exception4', command_coverage, module)

    content += """
                <table>
                    <thead>
                    <tr>
                        <th>Module</th>
                        <th>Untested</th>
                    </tr>
                    </thead>
                    <tbody>    """

    for cmd in all_untested_commands:
        content += """
          <tr>
            <td>{}</td>
            <td>{}</td>
          </tr>
        """.format(module, cmd)

    content += """
                    </tbody>
                </table>
                <p class="contact">This is command coverage report of {} module.<br>
                    Any question please contact Azure Cli Team.<br>
                </p>
            </div>
        </div><!-- /container -->
    </body>
</html>
    """.format(module)
    return content


def _render_td(table, color, percentage):
    """
    :param table:
    :param color:
    :param percentage:
    :return: Return a HTML table data
    """
    if color == 'N/A':
        table += """
                    <td name="td4">
                        <div style="text-align: center">N/A</div>
                    </td>
        """
    elif color != 'gold':
        table += """
                                        <td name="td4">
                                            <div class="single-chart">
                                                <svg viewBox="0 0 36 36" class="circular-chart {color}">
                                                    <path class="circle-bg"
                                                          d="M18 2.0845
                          a 15.9155 15.9155 0 0 1 0 31.831
                          a 15.9155 15.9155 0 0 1 0 -31.831"
                                                    />
                                                    <path class="circle"
                                                          stroke-dasharray="{percentage}, 100"
                                                          d="M18 2.0845
                          a 15.9155 15.9155 0 0 1 0 31.831
                          a 15.9155 15.9155 0 0 1 0 -31.831"
                                                    />
                                                    <text x="18" y="20.35" class="percentage">{percentage}%</text>
                                                </svg>
                                            </div>
                                        </td>                         
                    """.format(color=color, percentage=percentage)
    else:
        table += """
                        <td name="td4" class="medal">
                            <div class="ribbon"></div>
                            <div class="coin"></div>
                        </td>
        """
    return table


def _get_color(coverage):
    """
    :param coverage:
    :return: color and percentage
    """
    percentage = int(round(float(coverage[2][:-1]), 0)) if coverage[2] != 'N/A' else coverage[2]
    try:
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
    except Exception as e:
        print('coverage exception', coverage)
    return color, percentage


def get_html_path(date, level):
    """
    :param date:
    :return: html_path
    """
    root_path = get_azdev_repo_path()
    html_path = os.path.join(root_path, 'cmd_coverage', level, f'{date}')
    if not os.path.exists(html_path):
        os.makedirs(html_path)
    return html_path


def get_container_name():
    """
    Generate container name in storage account. It is also an identifier of the pipeline run.
    :return:
    """
    import datetime
    import random
    import string
    logger.warning('Enter get_container_name()')
    time = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    random_id = ''.join(random.choice(string.digits) for _ in range(6))
    name = time + '-' + random_id
    logger.warning('Exit get_container_name()')
    return name


def upload_files(container, html_path, account_key):
    """
    Upload html and json files to container
    :param container:
    :return:
    """
    logger.warning('Enter upload_files()')

    # Create container
    cmd = 'az storage container create -n {} --account-name clitestresultstac --account-key {} --public-access container'.format(container, account_key)
    os.system(cmd)

    # Upload files
    for root, dirs, files in os.walk(html_path):
        for name in files:
            if name.endswith('html') or name.endswith('css'):
                fullpath = os.path.join(root, name)
                cmd = 'az storage blob upload -f {} -c {} -n {} --account-name clitestresultstac'
                cmd = cmd.format(fullpath, container, name)
                logger.warning('Running: ' + cmd)
                os.system(cmd)

    logger.warning('Exit upload_files()')


if __name__ == '__main__':
    pass
    # _get_all_tested_commands(['a'], ['b'])
    # regex2()
    # regex3()
