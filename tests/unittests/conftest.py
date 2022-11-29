import pytest
import ast
from textwrap import dedent

pytest_plugins = "pytester"


@pytest.fixture
def makepyfile_and_add_meta(pytester, write_config):
    def wrapper(test_module_contents, viash_config, viash_executable):
        config_file = write_config(viash_config)
        to_insert = f"""\
             try:
                meta["config"] = "{str(config_file)}"
             except NameError:
                meta = {{"config": "{str(config_file)}"}}
             meta["executable"] = "{viash_executable}"
             """

        parsed_to_insert = ast.parse(dedent(to_insert))
        parsed_module_contents = ast.parse(dedent(test_module_contents))
        i = 0
        for i, elem in enumerate(parsed_module_contents.body):
            if isinstance(elem, (ast.Import, ast.ImportFrom)):
                continue
            break
        parsed_module_contents.body.insert(i, parsed_to_insert)
        pytester.makepyfile(ast.unparse(parsed_module_contents))
        return config_file

    return wrapper


@pytest.fixture
def write_config(pytester):
    def wrapper(viash_config):
        config_file = pytester.makefile(".vsh.yaml", config=viash_config)
        return config_file

    return wrapper


@pytest.fixture
def dummy_config():
    config = """
        functionality:
            name: foo
            description: |
                This is a dummy config for testing
        """
    return config


@pytest.fixture
def dummy_config_with_info():
    config = """
        functionality:
            name: foo
            description: |
                This is a dummy config for testing
        info:
            config: "/lorem/ipsum.vsh.config"
        """
    return config
