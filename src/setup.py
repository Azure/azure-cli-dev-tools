# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

"""Azure Developer Tools package that can be installed using setuptools"""


import os
from setuptools import setup

__VERSION__ = '0.1.0'


def read(fname):
    """Local read helper function for long documentation"""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='azdev',
    version=__VERSION__,
    description='Azure Developer Tools command line',
    url='https://github.com/Azure/azdev',
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
        'azdev.operations.tests',
        'azdev.operations.extensions',
        'azdev.utilities',
    ],
    install_requires=[
        'docutils',
        'flake8',
        'future',
        'gitpython',
        'knack~=0.5.1',
        'pylint==1.9.2',
        'pytest',
        'pytest-xdist',
        'tox',
        'virtualenv'
    ],
    package_data={'azdev.config': ['*.*']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['azdev=azdev:launch']
    }
)