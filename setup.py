# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

"""Azure Developer Tools package that can be installed using setuptools"""


import os
from setuptools import setup

__VERSION__ = '0.0.3'


def read(fname):
    """Local read helper function for long documentation"""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='azdev',
    version=__VERSION__,
    description='Azure Developer Tools command line',
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
        'azdev.operations.linter',
        'azdev.operations.linter.rules',
        'azdev.operations.tests',
        'azdev.operations.extensions',
        'azdev.utilities',
    ],
    install_requires=[
        'docutils',
        'flake8',
        'futures',
        'gitpython',
        'knack>=0.5.4',
        'mock',
        'pytest>=3.6.0',
        'pytest-xdist',
        'pyyaml',
        'requests',
        'tox',
        'wheel==0.30.0'
    ],
    extras_require={
        ":python_version<'3.0'": ['pylint==1.9.2'],
        ":python_version>='3.0'": ['pylint==2.3.0']
    },
    package_data={
        'azdev.config': ['*.*', 'cli_pylintrc', 'ext_pylintrc'],
        'azdev.operations.linter.rules': ['ci_exclusions.yml']
    },
    include_package_data=True,
    entry_points={
        'console_scripts': ['azdev=azdev.__main__:main']
    }
)