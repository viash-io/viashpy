from viashpy._run import viash_run
from viashpy.config import read_viash_config
from textwrap import dedent
import pytest


def test_viash_run_config_does_not_exist_raises():
    mesg = r"non_existant_config does not exist or is not a file\."
    with pytest.raises(FileNotFoundError, match=mesg):
        viash_run("non_existant_config", ["bar"])


def test_read_viash_config_empty_raises(pytester):
    mesg = r"The config file was empty\."
    empty_config = pytester.makefile(".vsh.yaml", foo="")
    with pytest.raises(ValueError, match=mesg):
        read_viash_config(empty_config)


def test_read_viash_config_not_map_raises(pytester):
    mesg = (
        r"Expected viash config to contain a map\. "
        r"Please make sure that providing a valid viash config yaml\."
    )
    config_contents = """
        - this
        - is
        - not
        - a viash config
        """
    empty_config = pytester.makefile(".vsh.yaml", foo=dedent(config_contents))
    with pytest.raises(ValueError, match=mesg):
        read_viash_config(empty_config)
