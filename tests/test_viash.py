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


def test_run_component_executes_subprocess(testdir):
    testdir.makepyfile(
        """
        import subprocess
        meta = {"executable": "foo"}

        def test_loading_run_component(mocker, run_component):
            mocker.patch('subprocess.check_output')
            run_component(["bar"])
            subprocess.check_output.assert_called_once_with(["foo", "bar"], stderr=subprocess.STDOUT)
        """
    )
    result = testdir.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_loading_run_component PASSED*",
        ]
    )
    assert result.ret == 0
