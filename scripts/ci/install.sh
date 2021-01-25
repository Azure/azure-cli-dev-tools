#!/usr/bin/env bash

set -ev

echo "Install azdev into virtual environment"
python -m venv env
source env/bin/activate
pip install -U pip setuptools wheel -q
pip install $(find ${BUILD_ARTIFACTSTAGINGDIRECTORY}/pypi -name *.tar.gz) -q
git clone https://github.com/Azure/azure-cli.git
git clone https://github.com/Azure/azure-cli-extensions.git
azdev setup -c azure-cli -r azure-cli-extensions
source env/bin/activate