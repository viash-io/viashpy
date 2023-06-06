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
    makepyfile_and_add_meta(
        f"""
        import subprocess
        from pathlib import Path

        def test_loading_run_component(mocker, run_component):
            mocked_check_output = mocker.patch('viashpy._run.check_output',
                                               return_value=b"Some dummy output")
            mocked_path = mocker.patch('viashpy.testing.Path.is_file', return_value=True)
            stdout = run_component(["bar"])
            mocked_check_output.assert_called_once_with({expected},
                                                        stderr=subprocess.STDOUT)
            assert stdout == b"Some dummy output"
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


def test_run_component_fails_logging(
    pytester, makepyfile_and_add_meta, dummy_config_with_info
):
    executable = pytester.makefile(
        "",
        foo="#!/bin/sh\npython -c 'import sys; raise RuntimeError(\"This script should fail\")'",
    )
    executable.chmod(executable.stat().st_mode | stat.S_IEXEC)

    makepyfile_and_add_meta(
        """
        import subprocess
        from pathlib import Path, PosixPath

        def test_loading_run_component(mocker, run_component):
            mocked_path = mocker.patch('viashpy.testing.Path.is_file', return_value=True)
            stdout = run_component(["bar"])
        """,
        dummy_config_with_info,
        executable,
    )
    result = pytester.runpytest()
    # Check if output from component is shown on error
    result.stdout.fnmatch_lines(
        [
            "*FAILED test_run_component_fails_logging.py::test_loading_run_component*",
        ]
    )
    result.stdout.fnmatch_lines(
        [
            "*This script should fail*",
        ]
    )
    # Check if stack traces are hidden
    result.stdout.no_fnmatch_line("*def wrapper*")
    result.stdout.no_fnmatch_line("*def run_component*")
    assert result.ret == 1


@pytest.mark.parametrize(
    "message_to_check, expected_outcome, expected_exitcode",
    [
        (
            "RuntimeError: This script should fail",
            "*test_run_component_fails_capturing.py::test_loading_run_component PASSED*",
            0,
        ),
        (
            "something_something_this_will_not_work",
            "*test_run_component_fails_capturing.py::test_loading_run_component FAILED*",
            1,
        ),
    ],
)
def test_run_component_fails_capturing(
    pytester,
    makepyfile_and_add_meta,
    dummy_config_with_info,
    message_to_check,
    expected_outcome,
    expected_exitcode,
):
    executable = pytester.makefile(
        "",
        foo="#!/bin/sh\npython -c 'import sys; raise RuntimeError(\"This script should fail\")'",
    )
    executable.chmod(executable.stat().st_mode | stat.S_IEXEC)

    makepyfile_and_add_meta(
        f"""
        import subprocess
        import pytest
        import re
        from pathlib import Path

        def test_loading_run_component(mocker, run_component):
            mocked_path = mocker.patch('viashpy.testing.Path.is_file', return_value=True)
            with pytest.raises(subprocess.CalledProcessError) as e:
                run_component(["bar"])
            assert re.search(r"{message_to_check}", e.value.stdout.decode('utf-8'))
        """,
        dummy_config_with_info,
        executable,
    )
    result = pytester.runpytest("-v")
    # Check if output from component is shown on error
    result.stdout.fnmatch_lines([expected_outcome])
    if expected_exitcode == 0:
        result.stdout.no_fnmatch_line("*This script should fail*")
    # Check if stack traces are hidden
    result.stdout.no_fnmatch_line("*def wrapper*")
    result.stdout.no_fnmatch_line("*def run_component*")
    assert result.ret == expected_exitcode
