.. :changelog:

Release History
===============

0.0.6
+++++
* `azdev test`: Fix issue where using `--profile` did not use the correct index.
                Changed the behavior to switch back to the original profile upon completion of tests.

0.0.5
+++++
* Fix issue where `azdev cli check-versions` did not accept the short form of a module name.
* Update `azdev cli check-versions` to allow modules as a positional argument, consistent with other azdev commands.
* Fix issue where `azdev test --discover` could result in a stack trace when a virtual environment exists within an extensions repo.

0.0.4
+++++
* Fix critical bug in `azdev setup`.

0.0.3
+++++
* Adds new commands `azdev extension build` and `azdev extension publish` to simplify extension publishing.
* Updates default exclusions for `azdev linter` when used on extensions.
* Adds a `--ci-exclusions` flag to `azdev linter` to emulate CI mode when run locally.
* Fix issue where `azdev test --discover` could result in a stack trace when a virtual environment exists within a cloned repo.
* Tweaks thresholds for `azdev per load-times`.

0.0.2
+++++

* Changes the behavior of `azdev test` to, by default, run tests on everything to be consistent with commands like `azdev style` and `azdev linter`.
* Removes `azdev verify version` and splits into two commands `azdev cli check-versions` and `azdev cli update-setup`.
* Various modifications to play nicely with azure-cli's CI build system.
* Revamps `azdev perf load-times` to reduce spurious failures.

0.0.1
++++++
* Initial release
