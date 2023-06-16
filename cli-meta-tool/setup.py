#!/usr/bin/env python

# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

"""Azure Command Meta Tools package that can be installed using setuptools"""

from setuptools import setup, find_packages
setup(name="cli-meta-tool",
      version='0.1.0',
      description="A tool for cli metadata management",
      long_description="A tool for cli metadata management",
      license='MIT',
      author='Microsoft Corporation',
      author_email='azpycli@microsoft.com',
      packages=find_packages(),
      include_package_data=True,
      install_requires=["deepdiff", "requests"],
      package_data={
        "cliMetaTool": ["data/*"]
      }
      )
