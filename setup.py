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
    long_description=README+ '\n\n' + HISTORY,
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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    keywords='azure',
    python_requires='>=2.7,!=3.4,!=3.3,!=3.2,!=3.1,!=3.0,<=3.8',
    packages=[
        'azdev',
        'azdev.config',
        'azdev.operations',
        'azdev.mod_templates',
        'azdev.operations.linter',
        'azdev.operations.linter.rules',
        'azdev.operations.tests',
        'azdev.operations.extensions',
        'azdev.utilities',
    ],
    install_requires=[
        'docutils',
        'flake8',
        'gitpython',
        'jinja2',
        'knack~=0.6.2',
        'mock',
        'pytest~=4.4.0',
        'pytest-xdist',
        'pyyaml',
        'requests',
        'tox',
        'wheel==0.30.0'
    ],
    extras_require={
        ":python_version<'3.0'": ['pylint==1.9.2', 'futures'],
        ":python_version>='3.0'": ['pylint==2.3.0']
    },
    package_data={
        'azdev.config': ['*.*', 'cli_pylintrc', 'ext_pylintrc'],
        'azdev.mod_templates': ['*.*'],
        'azdev.operations.linter.rules': ['ci_exclusions.yml']
    },
    include_package_data=True,
    entry_points={
        'console_scripts': ['azdev=azdev.__main__:main']
    }
)
