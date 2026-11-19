from subprocess import STDOUT, CalledProcessError
import os
import shutil
from pathlib import Path
import pytest
from viashpy import run_built_component
from viashpy._run import _get_viash_version


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


def test_run_built_component_relative_path_is_made_absolute(
    mocker, tmp_path, monkeypatch
):
    (tmp_path / "my_component").touch()
    monkeypatch.chdir(tmp_path)
    mocked_check_output = mocker.patch("viashpy._run.check_output")
    for component in ("./my_component", "my_component", Path("my_component")):
        mocked_check_output.reset_mock()
        run_built_component(component, [])
        mocked_check_output.assert_called_once_with(
            [tmp_path / "my_component"], stderr=STDOUT
        )


def test_run_built_component_viash_hub_version_check_uses_popen_kwargs(mocker):
    mocked_version = mocker.patch(
        "viashpy._run._get_viash_version", return_value=(0, 10, 0)
    )
    mocker.patch("viashpy._run.check_output")
    env = dict(os.environ, PATH="/opt/viash/bin")
    run_built_component("vsh://toolbox/yq", [], env=env, cwd="/proj", timeout=5)
    mocked_version.assert_called_once_with("viash", env=env, cwd="/proj", timeout=5)


@pytest.mark.parametrize(
    "popen_kwargs, output",
    [
        ({}, b"viash 0.10.0 (c) 2025 Data Intuitive\n"),
        ({"text": True}, "viash 0.10.0 (c) 2025 Data Intuitive\n"),
    ],
)
def test_get_viash_version_bytes_or_text_output(mocker, popen_kwargs, output):
    mocked_check_output = mocker.patch("viashpy._run.check_output", return_value=output)
    assert _get_viash_version("viash", **popen_kwargs) == (0, 10, 0)
    mocked_check_output.assert_called_once_with(["viash", "--version"], **popen_kwargs)


def _installed_viash_version():
    if shutil.which("viash") is None:
        return None
    try:
        return _get_viash_version("viash")
    except (CalledProcessError, ValueError):
        return None


_VIASH_VERSION = _installed_viash_version()


@pytest.mark.skipif(
    _VIASH_VERSION is None or _VIASH_VERSION < (0, 10, 0),
    reason="Running a component from Viash Hub requires viash 0.10.0 or newer "
    f"(found: {'.'.join(map(str, _VIASH_VERSION)) if _VIASH_VERSION else 'none'}).",
)
def test_run_built_component_viash_hub_executes(tmp_path):
    # Runs a real component from Viash Hub, without patching.
    # Needs network access and docker.
    input_file = tmp_path / "input.yaml"
    input_file.write_text("foo:\n  bar: hello from viash hub\n")
    output_file = tmp_path / "output.txt"
    run_built_component(
        "vsh://toolbox@v0.1.0/yq",
        [
            "--input",
            str(input_file),
            "--output",
            str(output_file),
            "--eval",
            ".foo.bar",
        ],
        cpus=1,
        memory="1GB",
    )
    assert output_file.read_text().strip() == "hello from viash hub"
