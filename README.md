# Microsoft Azure CLI Dev Tools (azdev)

[![Python](https://img.shields.io/pypi/pyversions/azure-cli.svg?maxAge=2592000)](https://pypi.python.org/pypi/azdev)
[![Build Status](https://dev.azure.com/azure-sdk/public/_apis/build/status/cli/Azure.azure-cli-dev-tools?branchName=master)](https://dev.azure.com/azure-sdk/public/_build/latest?definitionId=604&branchName=master)

The `azdev` tool is designed to aid new and experienced developers in contributing to Azure CLI command modules and extensions.

## Getting Started Videos

[1. Cloning Repos](https://azurecliprod.blob.core.windows.net/videos/01%20-%20CloningRepos.mp4)

[2. Setup with `azdev setup`](https://azurecliprod.blob.core.windows.net/videos/02%20-%20AzdevSetup.mp4)

[3. Basics with `azdev style/test/linter`](https://azurecliprod.blob.core.windows.net/videos/03%20-%20AzdevBasics.mp4)

[4. Creating modules with `azdev cli create`](https://azurecliprod.blob.core.windows.net/videos/04%20-%20AzdevCliCreate.mp4)

[5. Create extensions with `azdev extension create`](https://azurecliprod.blob.core.windows.net/videos/05%20-%20AzdevExtensionCreate.mp4)

[6. Publishing extensions with `azdev extension publish`](https://azurecliprod.blob.core.windows.net/videos/06%20-%20AzdevExtensionPublish.mp4)

## Setting up your development environment

1. Install Python 3.6/3.7/3.8 from http://python.org. Please note that the version of Python that comes preinstalled on OSX is 2.7. Currently it's not recommended to use Python 3.9.
2. Fork and clone the repository or repositories you wish to develop for.
    - For Azure CLI: https://github.com/Azure/azure-cli
    - For Azure CLI Extensions: https://github.com/Azure/azure-cli-extensions
    - Any other repository that you might have access to that contains CLI extensions.

    After forking `azure-cli`, follow the below commands to set up:
    ```Shell
    # Clone your forked repository
    git clone https://github.com/<your-github-name>/azure-cli.git

    cd azure-cli
    # Add the Azure/azure-cli repository as upstream
    git remote add upstream https://github.com/Azure/azure-cli.git
    git fetch upstream
    # Reset the default dev branch to track dev branch of Azure/azure-cli so you can use it to track the latest azure-cli code.
    git branch dev --set-upstream-to upstream/dev
    # Develop with a new branch
    git checkout -b <feature_branch>
    ```
    You can do the same for `azure-cli-extensions` except that the default branch for it is `main`, run `git branch main --set-upstream-to upstream/main` instead.

    See [Authenticating with GitHub from Git](https://docs.github.com/github/getting-started-with-github/set-up-git#next-steps-authenticating-with-github-from-git) about caching your GitHub credentials in Git which is needed when you push the code.

    
3. Create a new virtual environment for Python in the root of your clone. You can do this by running:

    Python 3.6+ (all platforms):
    ```BatchFile
    python -m venv env
    ```
    or
    ```Shell
    python3 -m venv env
    ```

4. Activate the env virtual environment by running:

    Windows CMD.exe:
    ```BatchFile
    env\Scripts\activate.bat
    ```

    Windows Powershell:
    ```
    env\Scripts\activate.ps1
    ```

    OSX/Linux (bash):
    ```Shell
    source env/bin/activate
    ```

5. Prepare and install `azdev`

   If you're on Linux, install the dependency packages first by running:

   For apt packages:
   ```Bash
   sudo apt install gcc python3-dev
   ```
   For rpm packages:
   ```Bash
   sudo yum install gcc python3-devel 
   ```

   Otherwise you will have `psutil` installation issues (#269) when you setup `azure-cli` later.
  
   Upgrade `pip` on all platforms:
   ```
   python -m pip install -U pip
   ```
   Install `azdev`:
   ```
   pip install azdev
   ```

6. Complete setup by running:
   ```
   azdev setup
   ```
  
   This will launch the interactive setup process. You can also run with non-interactive options:
   ```
   azdev setup --cli /path/to/azure-cli --repo /path/to/azure-cli-extensions
   ```
   To see more non-interactive options, run `azdev setup --help`.

## Authoring commands and tests

If you are building commands based on a REST API SPEC from [azure-rest-api-specs](https://github.com/Azure/azure-rest-api-specs), you can leverage [aaz-dev-tools](https://github.com/Azure/aaz-dev-tools) to generate the commands. Otherwise you can run the following commands to create a code template:
```
azdev extension create <extension-name>
```
or
```
azdev cli create <module-name>
```

If you are working on an extension, before you can run its command, you need to install the extension from the source code by running:
```
azdev extension add <extension-name>
```

Run `az <command> --help` with your command groups or commands for a quick check on the command interface and help messages.

For instructions on manually writing the commands and tests, see more in 
- [Authoring Command Modules](https://github.com/Azure/azure-cli/tree/dev/doc/authoring_command_modules)
- [Authoring Extensions](https://github.com/Azure/azure-cli/blob/dev/doc/extensions/authoring.md)
- [Authoring Tests](https://github.com/Azure/azure-cli/blob/dev/doc/authoring_tests.md)

## Style, linter check and testing
1. Check code style (Pylint and PEP8):
    ```
    azdev style <extension-name/module-name>
    ```
2. Run static code checks of the CLI command table:
    ```
    azdev linter <extension-name/module-name>
    ```
3. Record or replay CLI tests:
    ```
    azdev test <extension-name/module-name>
    ```

    By default, test is running in `once` mode. If there are no corresponding recording files (in yaml format), it will run live tests and generate recording files. If recording files are found, the tests will be run in `playback` mode against the recording files. You can use `--live` to force a test run in `live` mode and regenerate the recording files.

## Submitting a pull request to merge the code

1. After committing your code locally, push it to your forked repository:
    ```
    git push --set-upstream origin <feature_branch>
    ```
2. Submit a PR to merge from the `feature_branch` of your repository into the default branch of [Azure/azure-cli](https://github.com/Azure/azure-cli) or [Azure/azure-cli-extensions](https://github.com/Azure/azure-cli-extensions) repositories. See [Submitting Pull Requests](https://github.com/Azure/azure-cli/tree/dev/doc/authoring_command_modules#submitting-pull-requests) and [Publish Extensions](https://github.com/Azure/azure-cli/blob/dev/doc/extensions/authoring.md#publish) for more details.

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
