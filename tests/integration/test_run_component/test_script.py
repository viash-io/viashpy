import pytest
import sys
from pathlib import Path
from io import StringIO
from ruamel.yaml import YAML
from contextlib import redirect_stdout, redirect_stderr
import uuid

### VIASH START # noqa: E266
meta = {
    "memory_gb": 6,
}
### VIASH END # noqa: E266


@pytest.fixture()
def random_config_path(tmp_path):
    def wrapper():
        unique_filename = f"{str(uuid.uuid4())}.vsh.yaml"
        temp_file = tmp_path / unique_filename
        return temp_file

    return wrapper


class TestRunExecutable:
    meta = meta

    def test_run_component(self, run_component):
        captured_output = run_component(["--output", "bar.txt"])
        with open("bar.txt", "r") as open_output_file:
            contents = open_output_file.read()
            assert contents == "foo!"
        assert (
            captured_output is not None
        ), "Some output from stdout or stderr should have been captured"
        assert b"This is a logging statement" in captured_output


class TestRunUsingConfig:
    meta = meta

    @pytest.fixture()
    def viash_source_config_path(self, random_config_path):
        yaml_interface = YAML(typ="safe", pure=True)
        yaml_interface.default_flow_style = False
        original_config = yaml_interface.load(
            Path(f"{meta['resources_dir']}/dummy_config.vsh.yaml")
        )
        del original_config["functionality"]["test_resources"]
        del original_config["functionality"]["resources"][1]
        result_path = random_config_path()
        yaml_interface.dump(original_config, result_path)
        return result_path

    def test_run_component_check_correct_memory_syntax(self, run_component):
        captured_output = run_component(["--output", "bar.txt"], platform="native")
        with open("bar.txt", "r") as open_output_file:
            contents = open_output_file.read()
            assert contents == "foo!"
        assert (
            captured_output is not None
        ), "Some output from stdout or stderr should have been captured"
        assert (
            b"--memory looks like a parameter but is not a defined parameter and will instead be treated as a positional argument"
            not in captured_output
        )


def run_pytest_and_capture_output():
    temp_stdout = StringIO()
    temp_stderr = StringIO()
    print(f"meta: {meta}")
    with redirect_stdout(temp_stdout), redirect_stderr(temp_stderr):
        exit_code = pytest.main(
            [__file__, "--log-cli-level", "DEBUG"], plugins=["viashpy"]
        )
    stdout_str = temp_stdout.getvalue()
    stderr_str = temp_stderr.getvalue()
    print(f"stdout: {stdout_str}\nstderr: {stderr_str}\nexit_code: {exit_code}")
    return stdout_str, stderr_str, exit_code


if __name__ == "__main__":
    assert (
        meta["memory_gb"] is not None
    ), "This test should be executed with some --memory set."

    stdout_str, stderr_str, exit_code = run_pytest_and_capture_output()
    assert (
        "Different values were defined in the 'meta' dictionary that limit memory, choosing the one with the smallest unit"
        not in stdout_str
    )

    sys.exit(exit_code)
