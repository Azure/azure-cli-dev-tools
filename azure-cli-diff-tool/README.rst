Microsoft Azure CLI Diff Tools (azure-cli-diff-tool)
=======================================================

The ``azure-cli-diff-tool`` is designed to aid azure-cli users in diffing metadata files to see its updates through historical versions for Azure CLI command modules and extensions.

Setting up your environment
+++++++++++++++++++++++++++++++++++++++

1. Install Python 3.6+ from http://python.org. Please note that the version of Python that comes preinstalled on OSX is 2.7.

3. Create a new virtual environment for Python in the root of your clone. You can do this by running:

    Python 3.6+ (all platforms):

    ::

        python -m venv env

    or:

    ::

        python3 -m venv env


4. Activate the env virtual environment by running:

    Windows CMD.exe:

    ::

        env\scripts\activate.bat

    Windows Powershell:

    ::

        env\scripts\activate.ps1


    OSX/Linux (bash):

    ::

        source env/bin/activate

5. Install ``azure-cli-diff-tool`` by running:

    ::

        pip install azure-cli-diff-tool

Reporting issues and feedback
+++++++++++++++++++++++++++++

If you encounter any bugs with the tool please file an issue in the `Issues <https://github.com/Azure/azure-cli-dev-tools/issues>`__ section of our GitHub repo.

Contribute Code
+++++++++++++++

This project has adopted the `Microsoft Open Source Code of Conduct <https://opensource.microsoft.com/codeofconduct/>`__.

For more information see the `Code of Conduct FAQ <https://opensource.microsoft.com/codeofconduct/faq/>`__ or contact `opencode@microsoft.com <mailto:opencode@microsoft.com>`__ with any additional questions or comments.

If you would like to become an active contributor to this project please
follow the instructions provided in `Microsoft Azure Projects Contribution Guidelines <http://azure.github.io/guidelines.html>`__.

License
+++++++

::

    Azure CLI Diff Tools (azure-cli-diff-tool)

    Copyright (c) Microsoft Corporation
    All rights reserved.

    MIT License

    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the ""Software""), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.::
