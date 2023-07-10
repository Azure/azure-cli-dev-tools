#!/usr/bin/env bash

set -ev

: "${BUILD_STAGINGDIRECTORY:?BUILD_STAGINGDIRECTORY environment variable not set}"
: "${BUILD_SOURCESDIRECTORY:=$(cd $(dirname $0); cd ../../; pwd)}"

cd "${BUILD_SOURCESDIRECTORY}"
cd ./azure-cli-diff-tool

echo "Build azure cli diff tool"
pip install -U pip setuptools wheel
python setup.py bdist_wheel -d "${BUILD_STAGINGDIRECTORY}"
python setup.py sdist -d "${BUILD_STAGINGDIRECTORY}"