#!/usr/bin/env bash

# Extract the version of the CLI from azdev's __init__.py file.
: "${BUILD_STAGINGDIRECTORY:?BUILD_STAGINGDIRECTORY environment variable not set}"

# __VERSION__ may be quoted with either ' or ", so strip both.
ver=$(sed -nE "s/^__VERSION__[[:space:]]*=[[:space:]]*['\"]([^'\"]+)['\"].*/\1/p" azdev/__init__.py)
: "${ver:?unable to extract __VERSION__ from azdev/__init__.py}"

echo "$ver" > "$BUILD_STAGINGDIRECTORY/version"
echo "$ver" > "$BUILD_STAGINGDIRECTORY/azdev-${ver}.txt"
