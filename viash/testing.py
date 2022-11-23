import pytest
import logging
from ._run import run_build_component

logger = logging.Logger(__name__)


@pytest.fixture
def run_component(request):
    test_module = request.node.parent.obj
    try:
        executable = test_module.meta["executable"]
    except AttributeError as e:
        raise RuntimeError(
            f"Could not find meta variable in module {test_module}. Please make sure it is defined."
        ) from e

    def wrapper(args_as_list):
        run_build_component(executable, args_as_list)

    return wrapper
