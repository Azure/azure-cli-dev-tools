# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

import os

from knack.log import get_logger
from knack.util import CLIError

from .command import py_cmd, quote_arg

try:
    import tomllib
except ImportError:  # pragma: no cover - Python 3.10 compatibility
    import tomli as tomllib

logger = get_logger(__name__)

SETUP_PY = 'setup.py'
PYPROJECT_TOML = 'pyproject.toml'


def get_package_config(package_dir):
    """Return the packaging configuration file for a source package.

    ``setup.py`` takes precedence while repositories transition incrementally.
    A ``pyproject.toml`` qualifies only when it declares packaging configuration
    through ``[build-system]`` or ``[project]``; tool-only files such as a
    ``[tool.ruff]`` configuration are deliberately ignored.
    """
    setup_path = os.path.join(package_dir, SETUP_PY)
    if os.path.isfile(setup_path):
        return setup_path

    pyproject_path = os.path.join(package_dir, PYPROJECT_TOML)
    if not os.path.isfile(pyproject_path):
        return None

    try:
        with open(pyproject_path, 'rb') as stream:
            pyproject = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as ex:
        raise CLIError("Unable to read packaging configuration '{}': {}".format(pyproject_path, ex))

    if 'build-system' in pyproject or 'project' in pyproject:
        return pyproject_path
    return None


def find_package_configs(root_paths):
    """Find packaging configuration files in immediate child directories.

    Azure CLI distributions live directly under ``src``. Restricting discovery
    to one level prevents nested tools and vendored projects from being treated
    as CLI distributions.

    A package whose configuration cannot be read is skipped rather than aborting
    discovery. Nearly every command resolves paths through this function, so an
    in-progress migration in one package must not break unrelated packages.
    """
    if isinstance(root_paths, str):
        root_paths = [root_paths]

    configs = []
    for root_path in root_paths:
        if not os.path.isdir(root_path):
            continue
        with os.scandir(root_path) as entries:
            package_dirs = sorted(
                (entry.path for entry in entries if entry.is_dir()),
                key=os.path.normcase,
            )
        for package_dir in package_dirs:
            try:
                package_config = get_package_config(package_dir)
            except CLIError as ex:
                logger.warning("Skipping '%s' during package discovery: %s", package_dir, ex)
                continue
            if package_config:
                configs.append(package_config)
    return configs


def build_package_wheel(package_dir, output_dir):
    """Build one wheel and return its path, preserving the legacy build path.

    Existing ``setup.py`` packages continue to use their current setuptools
    command. Pyproject-only packages use the public PEP 517 interface exposed by
    ``build``. Callers consume the resulting wheel identically in both cases.
    """
    package_config = get_package_config(package_dir)
    if not package_config:
        raise CLIError("No setup.py or packaging-enabled pyproject.toml found in '{}'".format(package_dir))

    os.makedirs(output_dir, exist_ok=True)
    existing_wheels = set(os.listdir(output_dir))
    if os.path.basename(package_config) == SETUP_PY:
        result = py_cmd(
            'setup.py bdist_wheel -d {}'.format(quote_arg(output_dir)),
            is_module=False,
            cwd=package_dir,
        )
    else:
        result = py_cmd(
            'build --wheel --outdir {} {}'.format(quote_arg(output_dir), quote_arg(package_dir)),
            cwd=package_dir,
        )
    if result.error:
        raise result.error  # pylint: disable=raising-bad-type

    built_wheels = [
        os.path.join(output_dir, filename)
        for filename in os.listdir(output_dir)
        if filename.endswith('.whl') and filename not in existing_wheels
    ]
    if len(built_wheels) != 1:
        raise CLIError("Expected one wheel for '{}', found {}".format(package_dir, len(built_wheels)))
    return built_wheels[0]
