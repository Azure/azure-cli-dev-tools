.. :changelog:

Release History
===============

0.1.4
++++++
* `azdev linter`: Fix issue with help example rule.
* `azdev style`: Omit namespace packages from core modules.
* `azdev verify document-map`: Updates to work correctly on Linux.

0.1.3
++++++
* `azdev linter`: Fix issue where certain installations would fail on `ci_exclusions.yml` not found.


0.1.2
++++++
* `azdev setup`: Fix regression where azure.cli could not be run after installation.

0.1.1
++++++
* `azdev cli/extension create`: Fix issue where supporting files were not included. Adjust generation logic.

0.1.0
++++++
* Update for compatability with azure-cli 2.0.68's new package structure.
* BREAKING CHANGE: Removed `azdev cli update-setup`. Package changes to azure-cli no longer require this.
* BREAKING CHANGE: `azdev verify history` and `azdev cli check-versions` no longer accept any arguments. Since there are
  now far fewer modules, these were deemed unnecessary.

0.0.6
++++++
* Added new commands `azdev cli create` and `azdev extension create` to scaffold new modules/extensions.
* `azdev setup`: Tweaks to interactive experience.
* `azdev test`: Fix issue where using `--profile` did not use the correct index.
                Changed the behavior to switch back to the original profile upon completion of tests.

0.0.5
++++++
* Fix issue where `azdev cli check-versions` did not accept the short form of a module name.
* Update `azdev cli check-versions` to allow modules as a positional argument, consistent with other azdev commands.
* Fix issue where `azdev test --discover` could result in a stack trace when a virtual environment exists within an extensions repo.

0.0.4
++++++
* Fix critical bug in `azdev setup`.

0.0.3
++++++
* Adds new commands `azdev extension build` and `azdev extension publish` to simplify extension publishing.
* Updates default exclusions for `azdev linter` when used on extensions.
* Adds a `--ci-exclusions` flag to `azdev linter` to emulate CI mode when run locally.
* Fix issue where `azdev test --discover` could result in a stack trace when a virtual environment exists within a cloned repo.
* Tweaks thresholds for `azdev per load-times`.

0.0.2
++++++

* Changes the behavior of `azdev test` to, by default, run tests on everything to be consistent with commands like `azdev style` and `azdev linter`.
* Removes `azdev verify version` and splits into two commands `azdev cli check-versions` and `azdev cli update-setup`.
* Various modifications to play nicely with azure-cli's CI build system.
* Revamps `azdev perf load-times` to reduce spurious failures.

0.0.1
++++++
* Initial release
