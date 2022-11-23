from stat import S_IEXEC


def test_run_component_fixture(testdir):
    """Make sure that pytest accepts our fixture."""

    # create a temporary pytest test module
    testdir.makepyfile(
        """
        from types import FunctionType
        meta = {"executable": "foo"}

        def test_loading_run_component(run_component):
            assert isinstance(run_component, FunctionType)
        """
    )

    # run pytest with the following cmd args
    result = testdir.runpytest("-v")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        [
            "*::test_loading_run_component PASSED*",
        ]
    )
    assert result.ret == 0


def test_run_component_no_meta_variable_raises(testdir):
    """
    Make sure the run_component fixture raises SubprocessError
    when the test module does not contain the meta variable.
    """
    testdir.makepyfile(
        """
        def test_loading_run_component(run_component):
            raise NotImplementedError
        """
    )

    # run pytest with the following cmd args
    result = testdir.runpytest("-v")

    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        [
            "*RuntimeError: Could not find meta variable in module*",
        ]
    )
    assert result.ret != 0


def test_run_component_executes_subprocess(pytester):
    executable = pytester.makefile("", foo="This is a dummy executable!")
    executable.chmod(executable.stat().st_mode | S_IEXEC)

    pytester.makepyfile(
        """
        import subprocess
        from pathlib import Path

        meta = {"executable": "foo"}

        def test_loading_run_component(mocker, run_component):
            mocked = mocker.patch('viash._run.check_output')
            run_component(["bar"])
            mocked.assert_called_once_with([Path("foo"), "bar"],
                                        stderr=subprocess.STDOUT)
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_loading_run_component PASSED*",
        ]
    )
    assert result.ret == 0


def test_run_component_file_not_executable_raises(pytester):
    pytester.makefile("", foo="")
    pytester.makepyfile(
        """
        import subprocess
        from pathlib import Path

        meta = {"executable": "foo"}

        def test_loading_run_component(mocker, run_component):
            mocked = mocker.patch('viash._run.check_output')
            run_component(["bar"])
            mocked.assert_called_once_with([Path("foo"), "bar"],
                                        stderr=subprocess.STDOUT)
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*PermissionError: foo is not executable.",
        ]
    )
    assert result.ret != 0


def test_run_component_executable_does_not_exist_raises(pytester):
    pytester.makepyfile(
        """
        import subprocess
        from pathlib import Path

        meta = {"executable": "foo"}

        def test_loading_run_component(mocker, run_component):
            mocked = mocker.patch('viash._run.check_output')
            run_component(["bar"])
            mocked.assert_called_once_with([Path("foo"), "bar"],
                                        stderr=subprocess.STDOUT)
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*ValueError: foo does not exist or is not a file.*",
        ]
    )
    assert result.ret != 0
