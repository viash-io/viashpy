def test_viash_executable_fixture_default(pytester):
    pytester.makepyfile(
        """
        def test_getting_viash_fixture(viash_executable):
            assert viash_executable == "viash"
        """
    )
    result = pytester.runpytest("-v")
    assert result.ret == 0


def test_viash_executable_fixture_overwrite(pytester):
    pytester.makepyfile(
        """
        import pytest

        @pytest.fixture
        def viash_executable():
            return "bin/viash"

        def test_getting_viash_fixture(viash_executable):
            assert viash_executable == "bin/viash"
        """
    )
    result = pytester.runpytest("-v")
    assert result.ret == 0
