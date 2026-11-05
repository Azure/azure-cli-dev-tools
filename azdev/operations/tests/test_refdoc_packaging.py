# -----------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# -----------------------------------------------------------------------------

from email.parser import BytesParser
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

from build import ProjectBuilder
from packaging.requirements import Requirement


class TestRefdocPackaging(unittest.TestCase):
    def test_built_wheel_contains_compatible_reference_documentation(self):
        # Build a clean copy so stale build/egg-info directories cannot conceal
        # missing packages or data files in the distribution declarations.
        root = Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            source = temporary / 'source'
            source.mkdir()
            for name in ('pyproject.toml', 'MANIFEST.in', 'README.rst', 'HISTORY.rst', 'LICENSE'):
                shutil.copy2(root / name, source / name)
            shutil.copytree(root / 'azdev', source / 'azdev',
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            wheel = ProjectBuilder(str(source)).build('wheel', str(temporary / 'dist'))
            installed = temporary / 'installed'
            with ZipFile(wheel) as archive:
                names = set(archive.namelist())
                prefix = 'azdev/operations/help/refdoc/'
                required = {
                    '__init__.py', 'conf.py', 'common/__init__.py', 'common/directives.py',
                    'cli_docs/__init__.py', 'cli_docs/helpgen.py', 'cli_docs/ind.rst',
                    'extension_docs/__init__.py', 'extension_docs/helpgen.py',
                    'extension_docs/ind.rst',
                }
                self.assertFalse({prefix + name for name in required} - names,
                                 'Reference documentation files are missing from the wheel')
                metadata_path = next(name for name in names if name.endswith('.dist-info/METADATA'))
                metadata = BytesParser().parsebytes(archive.read(metadata_path))
                dependencies = {requirement.name: requirement.specifier for requirement in
                                map(Requirement, metadata.get_all('Requires-Dist', []))}
                self.assertIn('1.4.1', dependencies['azure-multiapi-storage'])
                self.assertNotIn('1.5.0', dependencies['azure-multiapi-storage'])
                self.assertNotIn('1.6.0', dependencies['azure-multiapi-storage'])
                self.assertNotIn('1.6.7', dependencies['sphinx'])
                self.assertIn('7.0.0', dependencies['sphinx'])
                self.assertIn('9.0.0', dependencies['sphinx'])
                archive.extractall(installed)

            # Import the actual wheel payload, not the source checkout. The
            # Sphinx and publishing imports must work with resolved dependencies.
            probe = """
from pathlib import Path
import sys
sys.path.insert(0, sys.argv[1])
from docutils.parsers.rst import Directive
from sphinx.application import Sphinx
from azdev.operations.help.refdoc.common.directives import AbstractHelpGenDirective
from azdev.operations.help.refdoc.cli_docs import helpgen as cli_helpgen
from azdev.operations.help.refdoc.extension_docs import helpgen as extension_helpgen
from azure.multiapi.storage.v2018_11_09.blob import BlockBlobService
assert issubclass(AbstractHelpGenDirective, Directive)
assert Path(cli_helpgen.__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve())
assert Path(extension_helpgen.__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve())
assert callable(Sphinx) and callable(BlockBlobService)
"""
            subprocess.run([sys.executable, '-I', '-c', probe, str(installed)],
                           cwd=temporary, check=True)


if __name__ == '__main__':
    unittest.main()
