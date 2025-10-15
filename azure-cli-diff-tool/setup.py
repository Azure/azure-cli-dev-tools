#!/usr/bin/env python

# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

"""Azure Command Diff Tools package that can be installed using setuptools"""
import os
import re
from setuptools import setup, find_packages

diff_tool_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(diff_tool_path, 'azure_cli_diff_tool', '__init__.py'), 'r') as version_file:
    __VERSION__ = re.search(r'^__VERSION__\s*=\s*[\'"]([^\'"]*)[\'"]',
                            version_file.read(), re.MULTILINE).group(1)

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()
with open('HISTORY.rst', 'r', encoding='utf-8') as f:
    HISTORY = f.read()

setup(name="azure-cli-diff-tool",
      version=__VERSION__,
      description="A tool for cli metadata management",
      long_description=README + '\n\n' + HISTORY,
      license='MIT',
      author='Microsoft Corporation',
      author_email='azpycli@microsoft.com',
      packages=find_packages(),
      include_package_data=True,
      install_requires=["deepdiff~=8.6.1", "requests~=2.32.3"],
      package_data={
        "azure_cli_diff_tool": ["data/*"]
      }
      )
