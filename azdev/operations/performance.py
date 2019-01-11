# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import re

from knack.log import get_logger
from knack.util import CLIError

from azdev.utilities import (
    display, heading, subheading, cmd
)

logger = get_logger(__name__)

TOTAL = 'ALL'
DEFAULT_THRESHOLD = 10

# TODO: Treat everything as bubble instead of specific modules
# explicit thresholds that deviate from the default
THRESHOLDS = {
    'network': 30,
    'vm': 30,
    'batch': 30,
    'storage': 50,
    TOTAL: 300
}


def check_load_time(runs=3):
    heading('Module Load Performance')

    regex = r"[^']*'([^']*)'[\D]*([\d\.]*)"

    results = {TOTAL: []}
    # Time the module loading X times
    for i in range(0, runs + 1):
        lines = cmd('az -h --debug', show_stderr=True).result
        if i == 0:
            # Ignore the first run since it can be longer due to *.pyc file compilation
            continue

        try:
            lines = lines.decode().splitlines()
        except AttributeError:
            lines = lines.splitlines()
        total_time = 0
        for line in lines:
            if line.startswith('DEBUG: Loaded module'):
                matches = re.match(regex, line)
                mod = matches.group(1)
                val = float(matches.group(2)) * 1000
                total_time = total_time + val
                if mod in results:
                    results[mod].append(val)
                else:
                    results[mod] = [val]
        results[TOTAL].append(total_time)

    passed_mods = {}
    failed_mods = {}

    mods = sorted(results.keys())
    bubble_found = False
    for mod in mods:
        val = results[mod]
        mean_val = mean(val)
        stdev_val = pstdev(val)
        threshold = THRESHOLDS.get(mod) or DEFAULT_THRESHOLD
        statistics = {
            'average': mean_val,
            'stdev': stdev_val,
            'threshold': threshold,
            'values': val
        }
        if mean_val > threshold:
            if not bubble_found and mean_val < 30:
                # This temporary measure allows one floating performance
                # failure up to 30 ms. See issue #6224 and #6218.
                bubble_found = True
                passed_mods[mod] = statistics
            else:
                failed_mods[mod] = statistics
        else:
            passed_mods[mod] = statistics

    subheading('Results')
    if failed_mods:
        display('== PASSED MODULES ==')
        display_table(passed_mods)
        display('\nFAILED MODULES')
        display_table(failed_mods)
        raise CLIError("""
FAILED: Some modules failed. If values are close to the threshold, rerun. If values
are large, check that you do not have top-level imports like azure.mgmt or msrestazure
in any modified files.
""")

    display('== PASSED MODULES ==')
    display_table(passed_mods)
    display('\nPASSED: Average load time all modules: {} ms'.format(
        int(passed_mods[TOTAL]['average'])))


def mean(data):
    """Return the sample arithmetic mean of data."""
    n = len(data)
    if n < 1:
        raise ValueError('len < 1')
    return sum(data) / float(n)


def sq_deviation(data):
    """Return sum of square deviations of sequence data."""
    c = mean(data)
    return sum((x - c) ** 2 for x in data)


def pstdev(data):
    """Calculates the population standard deviation."""
    n = len(data)
    if n < 2:
        raise ValueError('len < 2')
    ss = sq_deviation(data)
    return (ss / n) ** 0.5


def display_table(data):
    display('{:<20} {:>12} {:>12} {:>12} {:>25}'.format('Module', 'Average', 'Threshold', 'Stdev', 'Values'))
    for key, val in data.items():
        display('{:<20} {:>12.0f} {:>12.0f} {:>12.0f} {:>25}'.format(
            key, val['average'], val['threshold'], val['stdev'], str(val['values'])))
