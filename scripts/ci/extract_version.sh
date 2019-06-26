#!/usr/bin/env bash

# Extract the version of the CLI from azdev's __init__.py file.
: "${BUILD_STAGINGDIRECTORY:?BUILD_STAGINGDIRECTORY environment variable not set}"

ver=`cat azdev/__init__.py | grep __VERSION__ | sed s/' '//g | sed s/'__VERSION__='// |  sed s/\"//g`
echo $ver > $BUILD_STAGINGDIRECTORY/version
echo $ver > $BUILD_STAGINGDIRECTORY/azdev-${ver}.txt