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
    result.assert_outcomes(passed=1)


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
    "memory_pb, memory_tb, memory_gb, memory_mb, memory_kb, memory_b, expected_bytes, expected_warning",
    [
        (
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            False,
        ),  # Not specified (running test script directly but no memory constraints set)
        (
            "None",
            "None",
            "None",
            "None",
            "None",
            "None",
            "None",
            False,
        ),  # Using viash test without --memory
        (
            6,
            6144,
            6291456,
            6442450944,
            6597069766656,
            None,
            6755399441055744,
            False,
        ),  # Memory specified and the same
        (
            None,
            None,
            3,
            6144,
            6291456,
            None,
            6442450944,
            True,
        ),  # Memory specified and different, pick the largest
        (None, None, 6, None, None, None, 6442450944, False),  # Only one specified
        (None, None, 6.5, None, None, None, 6979321856, False),
        (None, None, 3.5, 6144, 6291456, None, 6442450944, True),
        (None, None, 6, 6144.5, 6291456, None, 6442450944, True),
        (None, None, 6, 6144.5, 6291456.5, None, 6442451456, True),
    ],
)
def test_run_component_different_memory_specification_warnings(
    dummy_config,
    pytester,
    makepyfile_and_add_meta,
    memory_pb,
    memory_tb,
    memory_gb,
    memory_mb,
    memory_kb,
    memory_b,
    expected_bytes,
    expected_warning,
):
    expected_memory_args = ""
    memory_specifiers = [
        memory_pb,
        memory_tb,
        memory_gb,
        memory_mb,
        memory_kb,
        memory_b,
    ]
    memory_specifiers = [
        specifier for specifier in memory_specifiers if specifier != "None"
    ]
    if any(memory_specifiers):
        expected_memory_args = f', "--memory", "{expected_bytes}B"'
    expected = (
        '["viash", "run", Path(meta["config"]), "--", "bar"%s]' % expected_memory_args
    )
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
        dummy_config,
        "foo",
        memory_pb=memory_pb,
        memory_tb=memory_tb,
        memory_gb=memory_gb,
        memory_mb=memory_mb,
        memory_kb=memory_kb,
        memory_b=memory_b,
    )
    result = pytester.runpytest()
    expected_outcome_dict = (
        {"passed": 1, "warnings": 1} if expected_warning else {"passed": 1}
    )
    result.assert_outcomes(**expected_outcome_dict)
    if expected_warning:
        result.stdout.fnmatch_lines(
            [
                "*Different values were defined in the 'meta' dictionary that limit memory, choosing the one with the smallest unit.*"
            ]
        )
    assert result.ret == 0


@pytest.mark.parametrize("memory, expected_bytes", [(None, None), (6, 6442450944)])
@pytest.mark.parametrize("cpu", [None, 2])
@pytest.mark.parametrize(
    "config_fixture, expected, arg_prefix",
    [
        (
            "dummy_config",
            '["viash", "run", Path(meta["config"]), "--", "bar"%s%s]',
            "--",
        ),
        ("dummy_config_with_info", '[Path("foo"), "bar"%s%s]', "---"),
    ],
)
def test_run_component_executes_subprocess(
    request,
    pytester,
    makepyfile_and_add_meta,
    memory,
    expected_bytes,
    cpu,
    config_fixture,
    expected,
    arg_prefix,
):
    format_string = (
        f', "{arg_prefix}cpus", "{cpu}"' if cpu else "",
        f', "{arg_prefix}memory", "{expected_bytes}B"' if memory else "",
    )
    expected = expected % format_string
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
        cpu=cpu,
        memory_gb=memory,
    )
    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=1)


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
    result.assert_outcomes(failed=1)
    # Check if output from component is shown on error
    result.stdout.fnmatch_lines(
        [
            "*This script should fail*",
        ]
    )
    # Check if stack traces are hidden
    result.stdout.no_fnmatch_line("*def wrapper*")
    result.stdout.no_fnmatch_line("*def run_component*")


@pytest.mark.parametrize(
    "message_to_check, expected_outcome, should_fail",
    [
        (
            "RuntimeError: This script should fail",
            "*test_run_component_fails_capturing.py::test_loading_run_component PASSED*",
            False,
        ),
        (
            "something_something_this_will_not_work",
            "*test_run_component_fails_capturing.py::test_loading_run_component FAILED*",
            True,
        ),
    ],
)
def test_run_component_fails_capturing(
    pytester,
    makepyfile_and_add_meta,
    dummy_config_with_info,
    message_to_check,
    expected_outcome,
    should_fail,
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
    expected_outcome_dict = {"failed": 1} if should_fail else {"passed": 1}
    result.assert_outcomes(**expected_outcome_dict)

    # Check if output from component is shown on error
    result.stdout.fnmatch_lines([expected_outcome])
    # Check if stack traces are hidden
    result.stdout.no_fnmatch_line("*def wrapper*")
    result.stdout.no_fnmatch_line("*def run_component*")
