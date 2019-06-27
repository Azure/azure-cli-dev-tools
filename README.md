# Microsoft Azure CLI Dev Tools (azdev)

[![Python](https://img.shields.io/pypi/pyversions/azure-cli.svg?maxAge=2592000)](https://pypi.python.org/pypi/azdev)
[![Build Status](https://dev.azure.com/azure-sdk/public/_apis/build/status/cli/Azure.azure-cli-dev-tools?branchName=master)](https://dev.azure.com/azure-sdk/public/_build/latest?definitionId=604&branchName=master)

The `azdev` tool is designed to aid new and experienced developers in contributing to Azure CLI command modules and extensions.

## Setting up your development environment

1. Install Python 3.5+ or 2.7+ from http://python.org. Please note that the version of Python that comes preinstalled on OSX is 2.7.
2. Fork and clone the repository or repositories you wish to develop for.
    - For Azure CLI: https://github.com/Azure/azure-cli
    - For Azure CLI Extensions: https://github.com/Azure/azure-cli-extensions
    - Any other repository that you might have access to that contains CLI extensions.
3. Create a new virtual environment for Python in the root of your clone. You can do this by running:

    Python 3.5+ (all platforms):
    ```BatchFile
    python -m venv env
    ```
    or
    ```Shell
    python3 -m venv env
    ```

    Python 2.7+ (all platforms)
    ```Shell
    python -m virtualenv env
    ```

4. Activate the env virtual environment by running:

    Windows CMD.exe:
    ```BatchFile
    env\scripts\activate.bat
    ```

    Windows Powershell:
    ```
    env\scripts\activate.ps1
    ```

    OSX/Linux (bash):
    ```Shell
    source env/bin/activate
    ```

5. Install `azdev` by running:
  `pip install azdev`

6. Complete setup by running:
  `azdev setup`
  
  This will launch the interactive setup process. To see non-interactive options run `azdev setup -h`.

## Reporting issues and feedback

If you encounter any bugs with the tool please file an issue in the [Issues](https://github.com/Azure/azure-cli-dev-tools/issues) section of our GitHub repo.

## Contribute Code

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).

For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

If you would like to become an active contributor to this project please
follow the instructions provided in [Microsoft Azure Projects Contribution Guidelines](http://azure.github.io/guidelines.html).

## License

```
Azure CLI Dev Tools (azdev)

Copyright (c) Microsoft Corporation
All rights reserved.

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the ""Software""), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```
