#!/usr/bin/env bash

set -ev

: "${BUILD_STAGINGDIRECTORY:?BUILD_STAGINGDIRECTORY environment variable not set}"
: "${BUILD_SOURCESDIRECTORY:="$(dirname ${BASH_SOURCE[0]})/../../.."}"

cd $BUILD_SOURCESDIRECTORY

echo "Build azdev"
pip install -U pip setuptools wheel
python setup.py bdist_wheel sdist -d $BUILD_STAGINGDIRECTORY
