# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from email.parser import BytesParser
from pathlib import Path
import shutil
import tempfile
import unittest
from zipfile import ZipFile

from packaging.requirements import Requirement

from build import ProjectBuilder


class TestRefdocPackaging(unittest.TestCase):
    def test_wheel_contains_reference_documentation(self):
        # Build from a clean copy to avoid stale egg-info or build directories
        # making missing package declarations appear to work.
        root = Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source'
            source.mkdir()
            for name in ('pyproject.toml', 'MANIFEST.in', 'README.rst', 'HISTORY.rst', 'LICENSE'):
                shutil.copy2(root / name, source / name)
            shutil.copytree(root / 'azdev', source / 'azdev',
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            wheel = ProjectBuilder(str(source)).build('wheel', str(Path(directory) / 'dist'))
            with ZipFile(wheel) as archive:
                names = set(archive.namelist())
                prefix = 'azdev/operations/help/refdoc/'
                required = {
                    'conf.py', 'common/__init__.py', 'common/directives.py',
                    'cli_docs/__init__.py', 'cli_docs/helpgen.py', 'cli_docs/ind.rst',
                    'extension_docs/__init__.py', 'extension_docs/helpgen.py',
                    'extension_docs/ind.rst'
                }
                self.assertFalse({prefix + name for name in required} - names,
                                 'Reference documentation files are missing from the wheel')
                metadata_path = next(name for name in names if name.endswith('.dist-info/METADATA'))
                metadata = BytesParser().parsebytes(archive.read(metadata_path))
                dependencies = [Requirement(value) for value in metadata.get_all('Requires-Dist', [])]
                storage = next(value for value in dependencies if value.name == 'azure-multiapi-storage')
                self.assertIn('1.4.1', storage.specifier)
                self.assertNotIn('1.5.0', storage.specifier)
                self.assertNotIn('1.6.0', storage.specifier)
