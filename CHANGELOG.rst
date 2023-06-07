
Changelog
*********

0.3.2 (07/06/2023)
=================

Bug fixes
---------
* `run_component`: fixed adding the captured output to `CalledProcessError` object when a component execution fails. 

0.3.1 (06/06/2023)
================

Bug fixes
---------
* `run_component`: fix a bug where `pytest.fail` was used when running a component failed instead of using `CalledProcessError`.

0.3.0 (06/06/2023)
=================

Breaking changes
----------------
* `run_component`: when the component fails, stack traces from helper functions are no longer shown.

* `run_component`: component output captured from stderr and stdout is added to pytest output.

0.2.1 (03/02/2023)
=================

Bug fixes
---------
* `run_component` now returns captured stdout and stderr from the component run. 

0.2.0 (05/12/2022)
==================

New functionality
-----------------
* Added the `meta`, `viash_executable`, `test_module`, `meta_config_path`, `meta_config`, `viash_source_config_path` `viash_source_config` fixtures.
* `run_component` will now supports to execute `viash run` with the component config when running tests inline instead of using `viash test`, removing the need to rebuild components.
* Added utility to extract tar files.

Breaking changes
----------------
* Dropped support for python3.7 and python3.8
* Drop Windows support as viash uses WSL on Windows.
* The `run_component` fixture now raises `AttributeError` instead of `RuntimeError` when the meta variable is not defined in the test module.
* `run_component` will now use `FileNotFoundError` instead of `RuntimeError` when trying to run an executable and this executable is not a file.


0.1.0 (23/10/2022)
==================
* Initial release
