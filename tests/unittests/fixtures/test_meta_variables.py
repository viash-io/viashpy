def test_get_meta_dict(pytester):
    pytester.makepyfile(
        """
        import sys
        meta = {}

        def test_get_meta_dict(meta):
            this_mod = sys.modules[__name__]
            nonlocal_meta = this_mod.meta
            assert id(meta) == id(nonlocal_meta)
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_get_meta_dict PASSED*",
        ]
    )
    assert result.ret == 0


def test_get_meta_executable(pytester):
    pytester.makepyfile(
        """
        meta = {"executable": "foo"}

        def test_get_executable(executable):
            assert executable == "foo"
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_get_executable PASSED*",
        ]
    )
    assert result.ret == 0


def test_get_meta_executable_not_found_raises(pytester):
    pytester.makepyfile(
        """
        meta = {}

        def test_get_executable(executable):
            raise NotImplementError
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*KeyError: \"Could not find 'executable' key in 'meta' variable of test module*",
        ]
    )
    assert result.ret != 0


def test_meta_not_defined_raises(pytester):
    pytester.makepyfile(
        """
        def test_meta_not_defined_raises(meta):
            raise NotImplementedError
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*AttributeError: Could not find meta variable in module*",
        ]
    )
    assert result.ret != 0


def test_meta_config_path(pytester):
    pytester.makepyfile(
        """
        from pathlib import Path
        meta = {"config": "/lorem/ipsum/bar.vsh.yaml"}

        def test_get_config_path(meta_config_path):
            assert meta_config_path == Path("/lorem/ipsum/bar.vsh.yaml")
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_get_config_path PASSED*",
        ]
    )
    assert result.ret == 0


def test_meta_config_path_not_defined_raises(pytester):
    pytester.makepyfile(
        """
        from pathlib import Path
        meta = {}

        def test_get_config_path(meta_config_path):
            assert meta_config_path == Path("/lorem/ipsum/bar.vsh.yaml")
        """
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*KeyError: \"The 'config' value was not set in the 'meta' dictionairy of the test module *",
        ]
    )
    assert result.ret != 0


def test_viash_source_config_path(pytester, dummy_config, makepyfile_and_add_meta):
    makepyfile_and_add_meta(
        """
        from pathlib import Path

        def test_get_config_path(viash_source_config_path):
            assert viash_source_config_path == Path(meta['config'])
        """,
        dummy_config,
        "foo",
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_get_config_path PASSED*",
        ]
    )
    assert result.ret == 0


def test_viash_source_config(pytester, dummy_config, makepyfile_and_add_meta):
    makepyfile_and_add_meta(
        """
        expected = {"functionality": {"name": "foo",
                                      "description": "This is a dummy config for testing"}
                    }

        def test_get_source_config(viash_source_config):
            assert viash_source_config == expected
        """,
        dummy_config,
        "foo",
    )
    result = pytester.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*::test_get_source_config PASSED*",
        ]
    )
    assert result.ret == 0
