import pytest
import ast
from textwrap import dedent
from pathlib import Path
import tarfile


@pytest.fixture
def makepyfile_and_add_meta(pytester, write_config):
    def wrapper(
        test_module_contents, viash_config, viash_executable, cpu=None, memory_gb=None
    ):
        config_file = write_config(viash_config)
        to_insert = dedent(
            f"""\
        try:
            meta["config"] = "{str(config_file)}"
        except NameError:
            meta = {{"config": "{str(config_file)}"}}
        meta["executable"] = "{viash_executable}"
        """
        )
        if cpu:
            to_insert += dedent(
                f"""\
            meta["cpus"] = {cpu}
            """
            )
        if memory_gb:
            to_insert += dedent(
                f"""\
            meta["memory_gb"] = "{memory_gb}"
            """
            )

        parsed_to_insert = ast.parse(to_insert)
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


@pytest.fixture(params=["gz", "xz", "bz2"])
def compression_extension(request):
    return request.param


@pytest.fixture()
def tarfile_with_one_root_dir(tmp_path, compression_extension):
    folder_to_add = Path(tmp_path) / "bar"
    folder_to_add.mkdir()
    file_to_add = folder_to_add / "foo.txt"
    with (file_to_add).open("w") as open_file_to_add:
        open_file_to_add.write("This is a test file.")
    tar_path = tmp_path / "dummy.tar.gz"

    with tarfile.open(tar_path, f"w:{compression_extension}") as open_tarfile:
        open_tarfile.add(
            str(folder_to_add),
            recursive=True,
            arcname=folder_to_add.relative_to(tmp_path),
        )
    return tar_path


@pytest.fixture()
def tarfile_with_one_root_file(tmp_path, compression_extension):
    file_to_add = tmp_path / "foo.txt"
    with (file_to_add).open("w") as open_file_to_add:
        open_file_to_add.write("This is a test file.")

    tar_path = tmp_path / "dummy.tar.gz"
    with tarfile.open(tar_path, f"w:{compression_extension}") as open_tarfile:
        open_tarfile.add(
            str(file_to_add), recursive=True, arcname=file_to_add.relative_to(tmp_path)
        )
    return tar_path


@pytest.fixture()
def tarfile_mixed_contents(tmp_path, compression_extension):
    folder_to_add = Path(tmp_path) / "root"
    folder_to_add.mkdir()
    subfolder = folder_to_add / "bar"
    subfolder.mkdir()
    file_to_add = subfolder / "foo.txt"
    with (file_to_add).open("w") as open_file_to_add:
        open_file_to_add.write("This is a test file.")
    tar_path = tmp_path / "dummy.tar.gz"
    root_file_to_add = folder_to_add / "lorem.txt"
    with root_file_to_add.open("w") as open_file_to_add:
        open_file_to_add.write("ipsum")
    with tarfile.open(tar_path, f"w:{compression_extension}") as open_tarfile:
        open_tarfile.add(
            str(folder_to_add),
            recursive=True,
            arcname=folder_to_add.relative_to(tmp_path),
        )
    return tar_path
