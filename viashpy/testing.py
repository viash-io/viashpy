import pytest
import logging
from ._run import run_build_component, viash_run, tobytesconverter
from .types import Engine, Platform
from .config import read_viash_config
from pathlib import Path
from functools import wraps
from subprocess import CalledProcessError
from __future__ import annotations
import warnings

logger = logging.getLogger(__name__)


@pytest.fixture
def test_module(request):
    return request.node.parent.obj


@pytest.fixture
def viash_executable():
    return "viash"


@pytest.fixture
def meta(test_module):
    try:
        return test_module.meta
    except AttributeError as e:
        raise AttributeError(
            f"Could not find meta variable in module {test_module}. Please make sure it is defined."
        ) from e


@pytest.fixture
def executable(meta_attribute_getter):
    return meta_attribute_getter("executable")


@pytest.fixture
def cpus(meta_attribute_getter):
    try:
        return meta_attribute_getter("cpus")
    except KeyError:
        return None


@pytest.fixture
def memory_bytes(meta_attribute_getter):
    """
    Cover the different scenarios that can occur when memory requirements are set.

    1. All memory fields set to 'None' (i.e. viash (ns) test without `--memory` or all fields manually set to None in test script): return None
    2. All memory fields not defined (i.e. KeyError, only when not set in test script and not using viash (ns) test): return None
    3. All memory fields set (either by running viash (ns) test or setting them manually): return the bytes
    4. Multiple values set, but not all (manually in test script): return the value for the smallest unit, converted to bytes.
    5. 1 value set: return the value (manually in test script), converted to bytes.
    """
    all_memory_attributes = {}
    for suffix in tobytesconverter.AVAILABLE_UNITS():
        try:
            memory_value = meta_attribute_getter(f"memory_{suffix.lower()}")
            if memory_value is not None:
                assert isinstance(memory_value, int) or isinstance(
                    memory_value, float
                ), "The values for the memory resources set in the `meta` dictionary must be floats or integers."
                all_memory_attributes[suffix] = memory_value
        except KeyError:
            pass
    if not all_memory_attributes:
        return
    memory_bytes = {
        suffix: tobytesconverter(memory, suffix)
        for suffix, memory in all_memory_attributes.items()
    }
    if len(set(memory_bytes.values())) > 1:
        if len(tobytesconverter.AVAILABLE_UNITS()) != len(memory_bytes):
            # if not all units are set, the user probably specified the memory themselves multiple times...
            warnings.warn(
                "Different values were defined in the 'meta' dictionary that "
                f"limit memory, choosing the one with the smallest unit. Found: {memory_bytes}, "
                f"available units: {tobytesconverter.AVAILABLE_UNITS()}."
            )
        for unit in tobytesconverter.AVAILABLE_UNITS():
            try:
                return f"{int(memory_bytes[unit])}B"
            except KeyError:
                pass
        raise RuntimeError("At least one available unit should have been found.")
    (_, unit_value), *_ = memory_bytes.items()
    return f"{int(unit_value)}B"


@pytest.fixture
def meta_attribute_getter(meta, test_module):
    def get_meta_attribute(attr):
        try:
            return meta[attr]
        except KeyError as e:
            raise KeyError(
                f"Could not find '{attr}' key in 'meta' variable of test module {test_module}. "
                "Please make sure it is defined."
            ) from e

    return get_meta_attribute


@pytest.fixture
def meta_config_path(meta_attribute_getter, test_module):
    try:
        config_path = meta_attribute_getter("config")
    except KeyError:
        raise KeyError(
            f"The 'config' value was not set in the 'meta' dictionary of the test module {test_module}."
            "Please define it between the '### VIASH_START ... ### VIASH_END' block."
            "In case this error is reported while using 'viash test' or 'viash_test', "
            "use a viash version >= 0.6.4."
        )
    return Path(config_path)


@pytest.fixture
def meta_config(meta_config_path):
    return read_viash_config(meta_config_path)


@pytest.fixture
def viash_source_config_path(meta_config_path, meta_config):
    """
    The config from the meta variable can either be a parsed config, meaning
    that the test is being run as a result from running 'viash test'/
    'viash_test' or the 'source' config as defined by the user.
    From a parsed config, the path to the original config source can be
    retreived from .['info']['config'] keys.
    """
    try:
        # meta_config is a parsed viash config, retreive the location of the source
        return Path(meta_config["info"]["config"])
    except KeyError:
        # viash >= 0.9 defines build_info instead of info
        try:
            return Path(meta_config["build_info"]["config"])
        except KeyError:
            # If .['info']['config'] or .['build_info']['config'] is not defined,
            # assume that the config is a source config
            return meta_config_path


@pytest.fixture
def viash_source_config(viash_source_config_path):
    return read_viash_config(viash_source_config_path)


@pytest.fixture
def run_component(
    caplog, executable, viash_source_config_path, viash_executable, cpus, memory_bytes
):
    """
    Returns a function that allows the user to run a viash component.
    The function will use 'viash run' to execute the component or run
    the executable (the build component), depending wether or not the
    test is executed inline or as a result of using 'viash test'.
    This has the benefit of using the latest changes from the source code
    when testing the component inline without manually needing to rebuild.

    If the test module defines meta['config'] which points to an existing file,
    the function will use 'viash run' to run the component. In contrast,
    if meta['config'] is a parsed config (as a result of executing
    tests using 'viash test'), the build component executable will be used
    instead.
    """
    __tracebackhide__ = True

    def run_and_handle_errors(function_to_run):
        @wraps(function_to_run)
        def wrapper(*args, **kwargs):
            __tracebackhide__ = True
            try:
                return function_to_run(*args, **kwargs)
            except CalledProcessError as e:
                with caplog.at_level(logging.DEBUG):
                    logger.info(
                        f"Captured component output was:\n{e.stdout.decode('utf-8')}"
                    )
                    # Create a new CalledProcessError object. This removes verbosity from the original object
                    raise e.with_traceback(None) from None

        return wrapper

    if viash_source_config_path.is_file():

        @run_and_handle_errors
        def wrapper(
            args_as_list, engine: Engine | None = None, platform: Platform | None = None
        ):
            return viash_run(
                viash_source_config_path,
                args_as_list,
                viash_location=viash_executable,
                cpus=cpus,
                memory=memory_bytes,
                engine=engine,
                platform=platform,
            )

        return wrapper

    logger.debug(
        "Could not find the original viash config source. "
        "Assuming test script is run from 'viash test' or 'viash_test'."
    )

    @run_and_handle_errors
    def wrapper(args_as_list):
        return run_build_component(
            executable, args_as_list, cpus=cpus, memory=memory_bytes
        )

    return wrapper
