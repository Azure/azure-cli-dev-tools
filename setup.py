#!/usr/bin/env python

# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

"""Azure Developer Tools package that can be installed using setuptools"""

from codecs import open
import os
import re
from setuptools import setup, find_packages


azdev_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(azdev_path, 'azdev', '__init__.py'), 'r') as version_file:
    __VERSION__ = re.search(r'^__VERSION__\s*=\s*[\'"]([^\'"]*)[\'"]',
                            version_file.read(), re.MULTILINE).group(1)

with open('README.rst', 'r', encoding='utf-8') as f:
    README = f.read()
with open('HISTORY.rst', 'r', encoding='utf-8') as f:
    HISTORY = f.read()

setup(
    name='azdev',
    version=__VERSION__,
    description='Microsoft Azure CLI Developer Tools',
    long_description=README + '\n\n' + HISTORY,
    url='https://github.com/Azure/azure-cli-dev-tools',
    author='Microsoft Corporation',
    author_email='azpycli@microsoft.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ],
    keywords='azure',
    python_requires='>=3.6',
    packages=[
        'azdev',
        'azdev.config',
        'azdev.operations',
        'azdev.mod_templates',
        'azdev.operations.help',
        'azdev.operations.help.refdoc',
        'azdev.operations.linter',
        'azdev.operations.linter.rules',
        'azdev.operations.linter.pylint_checkers',
        'azdev.operations.testtool',
        'azdev.operations.extensions',
        'azdev.operations.statistics',
        'azdev.operations.command_change',
        'azdev.operations.breaking_change',
        'azdev.operations.cmdcov',
        'azdev.utilities',
    ],
    install_requires=[
        'azure-multiapi-storage',
        'docutils',
        'flake8',
        'gitpython',
        'jinja2',
        'knack',
        'pylint<4',
        'pytest-xdist',  # depends on pytest-forked
        'pytest-forked',
        'pytest>=5.0.0',
        'pyyaml',
        'requests',
        'sphinx==1.6.7',
        'tox',
        'jsbeautifier~=1.14.7',
        'deepdiff~=6.3.0',
        'azure-cli-diff-tool~=0.0.6',
        'packaging',
        'tqdm',
        'wheel==0.30.0',
        'microsoft-security-utilities-secret-masker~=1.0.0b4'
    ],
    package_data={
        'azdev.config': ['*.*', 'cli_pylintrc', 'ext_pylintrc'],
        'azdev.mod_templates': ['*.*'],
        'azdev.operations.linter.rules': ['ci_exclusions.yml'],
        'azdev.operations.linter': ["data/*"],
        'azdev.operations.cmdcov': ['*.*'],
        'azdev.operations.breaking_change': ['*.*'],
    },
    include_package_data=True,
    entry_points={
        'console_scripts': ['azdev=azdev.__main__:main']
    }
)
