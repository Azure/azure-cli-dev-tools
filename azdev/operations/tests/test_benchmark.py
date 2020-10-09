# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import random
from unittest import mock, TestCase
from math import sqrt

from knack.util import CLIError

from ..performance import (
    _benchmark_cmd_staticstic,
    _benchmark_load_all_commands,
    benchmark,
)


class TestBenchmarkStatistics(TestCase):
    def test_statistic_ok(self):

        rands = sorted([random.random() * 10 for _ in range(11)])

        max_num = round(rands[-1], 4)
        min_num = round(rands[0], 4)
        avg_num = round(sum(rands) / len(rands), 4)
        std_num = round(sqrt(sum([(t - avg_num) ** 2 for t in rands]) / len(rands)), 4)

        stats = _benchmark_cmd_staticstic(rands)

        self.assertEqual(stats["Max"], max_num)
        self.assertEqual(stats["Min"], min_num)
        self.assertEqual(stats["Avg"], avg_num)
        self.assertEqual(stats["Media"], round(rands[5], 4))
        self.assertEqual(stats["Std"], std_num)

    def test_statistic_data_in_different_length(self):
        even_length_data = sorted([random.random() * 10 for _ in range(10)])
        odd_length_data = sorted([random.random() * 10 for _ in range(11)])

        even_avg = round(sum(even_length_data) / len(even_length_data), 4)
        even_std = round(
            sqrt(
                sum((t - even_avg) ** 2 for t in even_length_data) / len(even_length_data)
            ),
            4,
        )

        odd_avg = round(sum(odd_length_data) / len(odd_length_data), 4)
        odd_std = round(
            sqrt(
                sum((t - odd_avg) ** 2 for t in odd_length_data) / len(odd_length_data)
            ),
            4,
        )

        even_stats = _benchmark_cmd_staticstic(even_length_data)
        self.assertEqual(even_stats["Std"], even_std)

        odd_stats = _benchmark_cmd_staticstic(odd_length_data)
        self.assertEqual(odd_stats["Std"], odd_std)

    def test_benchmark_wrong_data(self):
        with self.assertRaises(IndexError):
            _benchmark_cmd_staticstic([])


class TestBenchmarkCommands(TestCase):
    def test_load_all_commands_ok(self):
        try:
            from azure.cli.core import get_default_cli  # pylint: disable=unused-import
        except ImportError:
            self.skipTest("Azure CLI is not installed")

        commands = _benchmark_load_all_commands()

        for cmd in commands:
            self.assertTrue(cmd.endswith(" --help"))

    def test_load_all_commands_fail(self):
        import sys

        original_azure_cli_core_mod = sys.modules.get("azure.cli.core")
        sys.modules["azure.cli.core"] = None

        with self.assertRaisesRegex(CLIError, "Azure CLI is not installed") as e:
            _benchmark_load_all_commands()

        if original_azure_cli_core_mod:
            sys.modules["azure.cli.core"] = original_azure_cli_core_mod
        else:
            del sys.modules[
                "azure.cli.core"
            ]  # restore azure.cli.core to the unimported status


# class _MockedMapResultCounter:
#     def __init__(self, _, iterable):
#         self.iterable = iterable

#     def get(self, timeout=0):  # pylint: disable=unused-argument
#         print(self.iterable)
#         return [1] * len(self.iterable)


class _MockedPoolMapResult:
    def __init__(self, func, iterable):
        self.func = func
        self.iterable = iterable

        self._value = [self.func(i) for i in iterable]  # mocked results

    def get(self, timeout=0):  # pylint: disable=unused-argument
        return self._value


class TestBenchmark(TestCase):
    def test_benchmark_with_negative_runs(self):
        with self.assertRaisesRegex(CLIError, "Number of runs must be greater than 0."):
            benchmark([], -1)

    def test_benchmark_with_zero_runs(self):
        with self.assertRaisesRegex(CLIError, "Number of runs must be greater than 0."):
            benchmark([], 0)

    # def test_benchmark_commands_size_with_empty_input(self):
    #     """
    #     Empty commands would fetch all commands from commmand table.
    #     The result'size should be equal to the commands' size
    #     """

    #     with mock.patch(
    #         "multiprocessing.pool.Pool.map_async",  # pylint: disable=bad-continuation
    #         lambda self, _, iterable, chunksize=None, callback=None, error_callback=None: _MockedMapResultCounter(  # pylint: disable=bad-continuation
    #             _, iterable,
    #         ),
    #     ):
    #         result = benchmark([])

    #         self.assertEqual(len(result), len(_benchmark_load_all_commands()))

    def test_benchmark_with_help_command(self):
        with mock.patch(
            "azdev.operations.performance._benchmark_cmd_timer",  # pylint: disable=bad-continuation
            return_value=1,  # pylint: disable=bad-continuation
        ), mock.patch(
            "multiprocessing.pool.Pool.map_async",
            lambda self, func, iterable, chunksize=None, callback=None, error_callback=None: _MockedPoolMapResult(
                func, iterable
            ),  # pylint: disable=bad-continuation
        ):

            commands = ["network applicaiton-gateway create -h", "version", "find"]
            result = benchmark(commands=commands)

            self.assertEqual(len(result), 3)

    def test_benchmark_in_actual_running(self):
        with mock.patch(
            "multiprocessing.pool.Pool.map_async",  # pylint: disable=bad-continuation
            lambda self, func, iterable, chunksize=None, callback=None, error_callback=None: _MockedPoolMapResult(  # pylint: disable=bad-continuation
                func, iterable
            ),
        ):
            commands = ["version"]

            result = benchmark(commands=commands)

            self.assertEqual(len(result), 1)

            stats = result[0]

            self.assertIn("Max", stats)
            self.assertIn("Min", stats)
            self.assertIn("Media", stats)
            self.assertIn("Avg", stats)
            self.assertIn("Std", stats)
            self.assertIn("Runs", stats)
            self.assertEqual(stats["Runs"], 20)  # default value
            self.assertIn("Command", stats)

    def test_benchmark_with_specific_runs(self):
        with mock.patch(
            "multiprocessing.pool.Pool.map_async",  # pylint: disable=bad-continuation
            lambda self, func, iterable, chunksize=None, callback=None, error_callback=None: _MockedPoolMapResult(  # pylint: disable=bad-continuation
                func, iterable
            ),
        ):
            commands = [
                "network applicaiton-gateway create -h",
                "version",
                "storage create",
            ]

            result = benchmark(commands=commands, runs=5)

            self.assertEqual(len(result), 3)

            for r in result:
                self.assertEqual(r["Runs"], 5)

    # def test_benchmark_timeout(self):
    #     import time

    #     def mocked_benchmark_timeout_func(_):
    #         time.sleep(2)

    #     with mock.patch(
    #         "azdev.operations.performance._benchmark_cmd_timer",  # pylint: disable=bad-continuation
    #         side_effect=mocked_benchmark_timeout_func,  # pylint: disable=bad-continuation
    #     ), mock.patch(
    #         "multiprocessing.pool.Pool.map_async",  # pylint: disable=bad-continuation
    #         lambda self, func, iterable, chunksize=None, callback=None, error_callback=None: _MockedPoolMapResult(  # pylint: disable=bad-continuation
    #             func, iterable
    #         ),
    #     ):
    #         commands = ["version"]

    #         benchmark(commands=commands)
