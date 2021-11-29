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
    CMD_PATTERN, QUO_PATTERN, END_PATTERN, EXCLUDE_MOD, RED, ORANGE, GREEN, BLUE, GOLD, RED_PCT, ORANGE_PCT,
    GREEN_PCT, BLUE_PCT)


logger = get_logger(__name__)


# pylint:disable=too-many-locals, too-many-statements, too-many-branches
def run_cmdcov(modules=None, git_source=None, git_target=None, git_repo=None, include_whl_extensions=False,
               save_global_exclusion=False):
    """
    :param modules:
    :param git_source:
    :param git_target:
    :param git_target:
    :return: None
    """
    require_azure_cli()
    #
    from azure.cli.core import get_default_cli  # pylint: disable=import-error
    from azure.cli.core.file_util import (  # pylint: disable=import-error
        get_all_help, create_invoker_and_load_cmds_and_args)

    heading('CLI Command Coverage')

    # allow user to run only on CLI or extensions
    cli_only = modules == ['CLI']
    ext_only = modules == ['EXT']
    if cli_only or ext_only:
        modules = None

    # needed to remove helps from azdev
    azdev_helps = helps.copy()
    exclusions = {}
    selected_modules = get_path_table(include_only=modules, include_whl_extensions=include_whl_extensions)

    if cli_only:
        selected_modules['ext'] = {}
    if ext_only:
        selected_modules['mod'] = {}
        selected_modules['core'] = {}

    # used to upsert global exclusion
    update_global_exclusion = None
    if save_global_exclusion and (cli_only or ext_only):
        if cli_only:
            update_global_exclusion = 'CLI'
        elif ext_only:
            update_global_exclusion = 'EXT'

    # filter down to only modules that have changed based on git diff
    selected_modules = filter_by_git_diff(selected_modules, git_source, git_target, git_repo)

    if not any(selected_modules.values()):
        logger.warning('No commands selected to check.')

    # selected_mod_names = list(selected_modules['mod'].keys()) + list(selected_modules['core'].keys()) + \
    #                      list(selected_modules['ext'].keys())
    # selected_mod_paths = list(selected_modules['mod'].values()) + list(selected_modules['core'].values()) + \
    #                      list(selected_modules['ext'].values())

    selected_mod_names = list(selected_modules['mod'].keys())
    selected_mod_paths = list(selected_modules['mod'].values())
    # exclude mod
    # exclude_mod = EXCLUDE_MOD
    # for mod in exclude_mod:
    #     selected_mod_names.remove(mod)
    #     selected_mod_paths.remove('c:\\code\\azure-cli\\src\\azure-cli\\azure\\cli\\command_modules\\{}'.format(mod))
    # Other Errors TODO
    # selected_mod_names.remove('appservice')
    # selected_mod_paths.remove('c:\\code\\azure-cli\\src\\azure-cli\\azure\\cli\\command_modules\\appservice')
    # selected_mod_names.remove('batchai')
    # selected_mod_paths.remove('c:\\code\\azure-cli\\src\\azure-cli\\azure\\cli\\command_modules\\batchai')
    # dir not exist TODO
    # selected_mod_names.remove('interactive')
    # selected_mod_paths.remove('c:\\code\\azure-cli\\src\\azure-cli\\azure\\cli\\command_modules\\interactive')

    if selected_mod_names:
        display('Modules: {}\n'.format(', '.join(selected_mod_names)))

    # collect all rule exclusions
    for path in selected_mod_paths:
        exclusion_path = os.path.join(path, 'cmdcov_exclusions.yml')
        if os.path.isfile(exclusion_path):
            with open(exclusion_path, encoding='utf-8') as f:
                mod_exclusions = yaml.safe_load(f)
            merge_exclusion(exclusions, mod_exclusions or {})

    global_exclusion_paths = [os.path.join(get_cli_repo_path(), 'cmdcov_exclusions.yml')]
    try:
        global_exclusion_paths.extend([os.path.join(path, 'cmdcov_exclusions.yml')
                                       for path in (get_ext_repo_paths() or [])])
    except CLIError:
        pass
    for path in global_exclusion_paths:
        if os.path.isfile(path):
            with open(path, encoding=ENCODING) as f:
                mod_exclusions = yaml.safe_load(f)
            merge_exclusion(exclusions, mod_exclusions or {})

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

    # load yaml help
    help_file_entries = {}
    for entry_name, help_yaml in helps.items():
        # ignore help entries from azdev itself, unless it also coincides
        # with a CLI or extension command name.
        if entry_name in azdev_helps and entry_name not in command_loader.command_table:
            continue
        help_entry = yaml.safe_load(help_yaml)
        help_file_entries[entry_name] = help_entry

    # trim command table and help to just selected_modules
    command_loader, help_file_entries = filter_modules(
        command_loader, help_file_entries, modules=selected_mod_names, include_whl_extensions=include_whl_extensions)

    if not command_loader.command_table:
        logger.warning('No commands selected to check.')
    display('command_loader: {}\n'.format(command_loader))

    all_test_commands = _get_all_commands(selected_mod_names, loaded_help)
    all_tested_commands = _get_all_tested_commands(selected_mod_names, selected_mod_paths)
    command_coverage, all_untested_commands = _run_commands_coverage(all_test_commands, all_tested_commands)
    html_file = _render_html(command_coverage, all_untested_commands)

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


def _get_all_commands(selected_mod_names, loaded_help):
    """
    :param selected_mod_names:
    :param loaded_help:
    :return: all_test_commands
    """
    # selected_mod_names = ['vm']
    exclude_parameters = []
    global_parameters = GLOBAL_PARAMETERS
    generic_update_parameters = GENERIC_UPDATE_PARAMETERS
    wait_condition_parameters = WAIT_CONDITION_PARAMETERS
    other_parameters = OTHER_PARAMETERS
    exclude_parameters = exclude_parameters + global_parameters + generic_update_parameters + wait_condition_parameters + other_parameters


    all_test_commands = {m: [] for m in selected_mod_names}
    # like module vm have multiple command like vm vmss disk snapshot
    for _, y in loaded_help.items():
        # if x.split()[0] in selected_mod_names:
        if hasattr(y, 'command_source') and y.command_source in selected_mod_names:
            for parameter in y.parameters:
                opt_list = []
                for opt in parameter.name_source:
                    if opt.startswith('-') and opt not in exclude_parameters:
                        opt_list.append(opt)
                if opt_list:
                    all_test_commands[y.command_source].append(f'{y.command} {opt_list}')

    return all_test_commands


def _get_all_tested_commands(selected_mod_names, selected_mod_path):
    """
    :param selected_mod_names:
    :param selected_mod_path:
    :return: all_tested_commands
    """
    import re
    cmd_pattern = CMD_PATTERN
    quo_pattern = QUO_PATTERN
    end_pattern = END_PATTERN
    # selected_mod_names = ['vm']
    all_tested_commands = {m: [] for m in selected_mod_names}
    # selected_mod_path = ['c:\\code\\azure-cli\\src\\azure-cli\\azure\\cli\\command_modules\\vm']
    # selected_mod_path = ['d:\\code\\azure-cli\\src\\azure-cli\\azure\\cli\\command_modules\\vm']
    for idx, path in enumerate(selected_mod_path):
        test_dir = os.path.join(path, 'tests')
        # test_dir = os.path.join(path, 'tests', 'latest')
        files = find_files(test_dir, 'test_*.py')
        # files = filter(lambda f: f.startswith('test_'), os.listdir(test_dir))
        for f in files:
            # if f != 'test_image_builder_commands.py':
            # if f != 'test_vm_commands.py':
            #     continue
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
                    if re.findall(cmd_pattern, lines[row_num]):
                        command = re.findall(cmd_pattern, lines[row_num])[0][0]
                        while row_num < total_lines and not re.findall(end_pattern, lines[row_num]):
                            row_num += 1
                            try:
                                command += re.findall(quo_pattern, lines[row_num])[0][1]
                            except Exception as e:
                                # pass
                                print('Exception1', row_num, selected_mod_names[idx], f)
                        else:
                            command = command + ' ' + str(count)
                            all_tested_commands[selected_mod_names[idx]].append(command)
                            row_num += 1
                            count += 1
                    else:
                        row_num += 1
    return all_tested_commands


def _run_commands_coverage(all_test_commands, all_tested_commands):
    """
    :param all_test_commands:
    :param all_untested_commands:
    :return: command_coverage and all_untested_commands
    """
    import ast
    # module: vm
    # percentage: xx.xx%
    # all_untested_commands: {'vm': []}
    command_coverage = {'Total': [0, 0, 0]}
    all_untested_commands = {}
    for module in all_test_commands.keys():
        command_coverage[module] = []
        all_untested_commands[module] = []
    for module in all_test_commands.keys():
        count = 0
        for command in all_test_commands[module]:
            exist_flag = False
            prefix, opt_list = command.rsplit('[', maxsplit=1)[0], ast.literal_eval('[' + command.rsplit('[', maxsplit=1)[1])
            for cmd in all_tested_commands[module]:
                if prefix in cmd:
                    for opt in opt_list:
                        if opt in cmd:
                            count += 1
                            exist_flag = True
                            if exist_flag:
                                break
                if exist_flag:
                    break
            else:
                all_untested_commands[module].append(command)
        try:
            command_coverage[module] = [count, len(all_untested_commands[module]), f'{count / len(all_test_commands[module]):.3%}']
        except:
            print('Exception2', module)
        command_coverage['Total'][0] += count
        command_coverage['Total'][1] += len(all_untested_commands[module])
    command_coverage['Total'][2] = f'{command_coverage["Total"][0] / (command_coverage["Total"][0] + command_coverage["Total"][1]):.3%}'
    logger.warning(command_coverage)
    return command_coverage, all_untested_commands


def _render_html(command_coverage, all_untested_commands):
    """
    :param command_coverage:
    :param all_untested_commands:
    :return: Return a HTML string
    """
    logger.warning('Enter render()')
    import time
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    html_path = get_html_path(date.split()[0])
    # css path
    source = os.path.join(get_azdev_repo_path(), 'azdev', 'operations', 'cmdcov', 'component.css')
    # adding exception handling
    try:
        shutil.copy(source, html_path)
    except IOError as e:
        print("Unable to copy css file %s" % e)
    except:
        print("Unexpected error:", sys.exc_info())
    content = """
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>CLI Command Coverage</title>
        <link rel="stylesheet" type="text/css" href="component.css"/>
        <link rel="shortcut icon" href="favicon.ico">
    </head>
<body>
    <div class="container">
        <div class="component">
            <h1>CLI Command Coverage Report</h1>
            <h2>Date: {}</h2>
    """.format(date)

    content += """
                <h2>Tested: {}, Untested: {}, Percentage: {}</h2>
                <p>This is the command coverage report of CLI. Scroll down to see the every module coverage.<br>
                    Any question please contact Azure Cli Team.</p>
    """.format(command_coverage['Total'][0], command_coverage['Total'][1], command_coverage['Total'][2])

    table = """
                <table>
                    <thead>
                    <tr>
                        <th>Module</th>
                        <th>Tested</th>
                        <th>Untested</th>
                        <th>Percentage</th>
                        <th>Percentage</th>
                        <th>Reports</th>
                    </tr>
                    </thead>
    """

    table += """
                    <tbody>
                    <tr>
                        <td>Total</td>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>

    """.format(command_coverage['Total'][0], command_coverage['Total'][1], command_coverage['Total'][2])

    color, percentage = _get_color(command_coverage['Total'])
    table = _render_td(table, color, percentage)

    table += """
                        <td>N/A</td>
                    </tr>
    """

    command_coverage.pop('Total')

    for module, coverage in command_coverage.items():
        # feedback: []
        # find: []
        if coverage:
            reports = '<a href="{module}.html">{module} coverage report</a> '.format(module=module)
            child_html = _render_child_html(module, coverage, all_untested_commands[module])
            with open(f'{html_path}/{module}.html', 'w', encoding='utf-8') as f:
                f.write(child_html)
            try:
                table += """
                  <tr>
                    <td>{}</td>
                    <td>{}</td>
                    <td>{}</td>
                    <td>{}</td>
                """.format(module, coverage[0], coverage[1], coverage[2])
            except:
                print('Exception3', module, coverage, reports)

            color, percentage = _get_color(coverage)
            table = _render_td(table, color, percentage)

            table += """
                                <td>{}</td>
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

    # copy icon
    source = os.path.join(get_azdev_repo_path(), 'azdev', 'operations', 'cmdcov', 'favicon.ico')
    # adding exception handling
    try:
        shutil.copy(source, html_path)
    except IOError as e:
        print("Unable to copy %s" % e)
    except:
        print("Unexpected error:", sys.exc_info())

    return index_html


def _render_child_html(module, command_coverage, all_untested_commands):
    """
    :param module:
    :param command_coverage:
    :param all_untested_commands:
    :return: Return a HTML string
    """
    import time
    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

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
            <div class="component">
                <h1>{module} Command Coverage Report</h1>
                <h2>Date: {date}</h2>
    """.format(module=module, date=date)

    try:
        content += """
                    <h2>Tested: {}, Untested: {}, Percentage: {}</h2>
                    <p>This is command coverage report of {} module. Scroll down to see the details.<br>
                        Any question please contact Azure Cli Team.<br>
                        <a href="index.html" title="Back to Summary">Back to Homepage</a>.</p>
        """.format(command_coverage[0], command_coverage[1], command_coverage[2], module)
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
                    <a href="index.html" title="Back to Summary">Back to Homepage</a>.</p>
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
    if color != 'gold':
        table += """
                                        <td>
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
                        <td class="medal">
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
    try:
        if coverage[2] < RED_PCT:
            color = RED
        elif coverage[2] < ORANGE_PCT:
            color = ORANGE
        elif coverage[2] < GREEN_PCT:
            color = GREEN
        elif coverage[2] < BLUE_PCT:
            color = BLUE
        else:
            color = GOLD
        percentage = coverage[2].split('.')[0]
    except Exception as e:
        print('coverage exception', coverage)
    return color, percentage


def get_html_path(date):
    """
    :param date:
    :return: html_path
    """
    root_path = get_azdev_repo_path()
    html_path = os.path.join(root_path, 'cmd_coverage', f'{date}')
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
