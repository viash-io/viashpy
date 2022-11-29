import stat
import pytest


def test_run_component_fixture(pytester, makepyfile_and_add_meta, dummy_config):
    """Make sure that pytest accepts our fixture."""

    makepyfile_and_add_meta(
        """
        import sys
        from types import FunctionType

        def test_loading_run_component(run_component):
            assert isinstance(run_component, FunctionType)
        """,
        dummy_config,
        "foo",
    )

    # run pytest with the following cmd args
    result = pytester.runpytest("-v")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        [
            "*::test_loading_run_component PASSED*",
        ]
    )
    assert result.ret == 0


def test_run_component_no_meta_variable_raises(pytester):
    """
    Make sure the run_component fixture raises SubprocessError
    when the test module does not contain the meta variable.
    """
    pytester.makepyfile(
        """
        def test_loading_run_component(run_component):
            raise NotImplementedError
        """
    )

    # run pytest with the following cmd args
    result = pytester.runpytest("-v")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        [
            "*AttributeError: Could not find meta variable in module*",
        ]
    )
    assert result.ret != 0


@pytest.mark.parametrize(
    "config_fixture, expected",
    [
        ("dummy_config", '["viash", "run", Path(meta["config"]), "--", "bar"]'),
        ("dummy_config_with_info", '[Path("foo"), "bar"]'),
    ],
)
def test_run_component_executes_subprocess(
    request, pytester, makepyfile_and_add_meta, config_fixture, expected
):
    executable = pytester.makefile("", foo="This is a dummy executable!")
    executable.chmod(executable.stat().st_mode | stat.S_IEXEC)

    makepyfile_and_add_meta(
        f"""
        import subprocess
        from pathlib import Path, PosixPath

        def test_loading_run_component(mocker, run_component):
            mocked_check_output = mocker.patch('viashpy._run.check_output')
            mocked_path = mocker.patch('viashpy.testing.Path.is_file', return_value=True)
            run_component(["bar"])
            mocked_check_output.assert_called_once_with({expected},
                                                        stderr=subprocess.STDOUT)
        """,
        request.getfixturevalue(config_fixture),
        "foo",
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_loading_run_component PASSED*",
        ]
    )
    assert result.ret == 0


def test_run_component_executable_does_not_exist_raises(
    pytester, makepyfile_and_add_meta, dummy_config_with_info
):
    makepyfile_and_add_meta(
        """
        import subprocess
        from pathlib import Path

        def test_loading_run_component(mocker, run_component):
            mocked = mocker.patch('viashpy._run.check_output')
            run_component(["bar"])
            mocked.assert_called_once_with([Path("foo"), "bar"],
                                        stderr=subprocess.STDOUT)
        """,
        dummy_config_with_info,
        "foo",
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*FileNotFoundError: foo does not exist or is not a file.*",
        ]
    )
    assert result.ret != 0
