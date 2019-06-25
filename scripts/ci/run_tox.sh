#!/usr/bin/env bash

set -ev

pip install tox
python -m tox
