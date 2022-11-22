import pytest
import subprocess
import logging

logger = logging.Logger(__name__)


@pytest.fixture
def run_component(request):
    test_module = request.node.parent.obj
    try:
        meta = test_module.meta
    except AttributeError as e:
        raise RuntimeError(
            f"Could not find meta variable in module {test_module}. Please make sure it is defined."
        ) from e

    def wrapper(args_as_list):
        subprocess.check_output(
            [meta["executable"]] + args_as_list, stderr=subprocess.STDOUT
        )

    return wrapper
