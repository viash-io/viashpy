import pytest
import logging
from ._run import run_build_component, viash_run
from .config import read_viash_config
from pathlib import Path

logger = logging.Logger(__name__)


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
def executable(meta, test_module):
    try:
        return meta["executable"]
    except KeyError as e:
        raise KeyError(
            f"Could not find 'executable' key in 'meta' variable of test module {test_module}. Please make sure it is defined."
        ) from e


@pytest.fixture
def meta_config_path(meta, test_module):
    try:
        config_path = meta["config"]
    except KeyError as e:
        raise KeyError(
            f"The 'config' value was not set in the 'meta' dictionairy of the test module {test_module}."
            "Please define it between the '### VIASH_START ... ### VIASH_END' block."
            "In case this error is reported while using 'viash test' or 'viash_test', "
            "use a viash version >= 0.6.4."
        ) from e
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
        # If .['info']['config'] is not defined, assume that the config is a source config
        return meta_config_path


@pytest.fixture
def viash_source_config(viash_source_config_path):
    return read_viash_config(viash_source_config_path)


@pytest.fixture
def run_component(executable, viash_source_config_path, viash_executable):
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
    if viash_source_config_path.is_file():

        def wrapper(args_as_list):
            return viash_run(
                viash_source_config_path, args_as_list, viash_location=viash_executable
            )

        return wrapper

    logger.info(
        "Could not find the original viash config source. "
        "Assuming test script is run from 'viash test' or 'viash_test'."
    )

    def wrapper(args_as_list):
        return run_build_component(executable, args_as_list)

    return wrapper
