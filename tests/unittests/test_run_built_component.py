from subprocess import STDOUT
import pytest
from viashpy import run_built_component


def test_run_built_component_executable_does_not_exist_raises():
    mesg = r"non_existant_executable does not exist or is not a file\."
    with pytest.raises(FileNotFoundError, match=mesg):
        run_built_component("non_existant_executable", ["bar"])


@pytest.mark.parametrize(
    "cpus, memory, expected_extra_args",
    [
        (None, None, []),
        (2, None, ["---cpus", "2"]),
        (None, "10GB", ["---memory", "10GB"]),
        (2, "10GB", ["---cpus", "2", "---memory", "10GB"]),
    ],
)
def test_run_built_component_executes_subprocess(
    mocker, tmp_path, cpus, memory, expected_extra_args
):
    executable = tmp_path / "my_component"
    executable.touch()
    mocked_check_output = mocker.patch(
        "viashpy._run.check_output", return_value=b"Some dummy output"
    )
    result = run_built_component(
        executable, ["--input", "foo"], cpus=cpus, memory=memory
    )
    assert result == b"Some dummy output"
    mocked_check_output.assert_called_once_with(
        [executable, "--input", "foo"] + expected_extra_args, stderr=STDOUT
    )


def test_run_built_component_invalid_memory_suffix_raises(tmp_path):
    executable = tmp_path / "my_component"
    executable.touch()
    with pytest.raises(AssertionError, match=r"The memory specifier must have"):
        run_built_component(executable, [], memory="10")


@pytest.mark.parametrize(
    "viash_location, cpus, memory, expected_extra_args",
    [
        ("viash", None, None, []),
        ("/opt/viash/bin/viash", 2, "10GB", ["---cpus", "2", "---memory", "10GB"]),
    ],
)
def test_run_built_component_viash_hub(
    mocker, viash_location, cpus, memory, expected_extra_args
):
    mocked_version = mocker.patch(
        "viashpy._run._get_viash_version", return_value=(0, 10, 0)
    )
    mocked_check_output = mocker.patch(
        "viashpy._run.check_output", return_value=b"Some dummy output"
    )
    result = run_built_component(
        "vsh://toolbox@v0.1.0/yq",
        ["--input", "foo"],
        cpus=cpus,
        memory=memory,
        viash_location=viash_location,
    )
    assert result == b"Some dummy output"
    mocked_version.assert_called_once_with(viash_location)
    mocked_check_output.assert_called_once_with(
        [viash_location, "run", "vsh://toolbox@v0.1.0/yq", "--", "--input", "foo"]
        + expected_extra_args,
        stderr=STDOUT,
    )


def test_run_built_component_viash_hub_old_viash_raises(mocker):
    mocker.patch("viashpy._run._get_viash_version", return_value=(0, 9, 4))
    mocked_check_output = mocker.patch("viashpy._run.check_output")
    mesg = (
        r"Running a component from Viash Hub \('vsh://toolbox/yq'\) requires "
        r"viash 0\.10\.0 or newer, found 0\.9\.4\."
    )
    with pytest.raises(ValueError, match=mesg):
        run_built_component("vsh://toolbox/yq", [])
    mocked_check_output.assert_not_called()
