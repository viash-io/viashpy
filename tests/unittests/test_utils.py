from viashpy.utils import extract_tar
import shutil
import pytest
from pathlib import Path


def test_extract_tar_one_root_dir(tmp_path, tarfile_with_one_root_dir):
    temp_output_folder = tmp_path / "test_extract_tar_output"
    temp_output_folder.mkdir()
    extracted_tar = extract_tar(tarfile_with_one_root_dir, temp_output_folder)
    assert extracted_tar == temp_output_folder / "dummy"
    assert (extracted_tar / "foo.txt").is_file()
    with (extracted_tar / "foo.txt").open("r") as open_file:
        assert "This is a test file." == open_file.read()


def test_extract_tar_one_root_file(tmp_path, tarfile_with_one_root_file):
    temp_output_folder = tmp_path / "test_extract_tar_output"
    temp_output_folder.mkdir()
    extracted_tar = extract_tar(tarfile_with_one_root_file, temp_output_folder)
    assert extracted_tar == temp_output_folder / "dummy"
    assert (extracted_tar / "foo.txt").is_file()
    with (extracted_tar / "foo.txt").open("r") as open_file:
        assert "This is a test file." == open_file.read()


def test_extract_tar_mixed(tmp_path, tarfile_mixed_contents):
    temp_output_folder = tmp_path / "test_extract_tar_output"
    temp_output_folder.mkdir()
    extracted_tar = extract_tar(tarfile_mixed_contents, temp_output_folder)
    assert extracted_tar == temp_output_folder / "dummy"
    assert (extracted_tar / "bar" / "foo.txt").is_file()
    with (extracted_tar / "bar" / "foo.txt").open("r") as open_file:
        assert "This is a test file." == open_file.read()


def test_extract_tar_no_extensions(tmp_path, tarfile_mixed_contents):
    temp_output_folder = tmp_path / "test_extract_tar_output"
    temp_output_folder.mkdir()
    tarfile_without_suffix = shutil.move(
        tarfile_mixed_contents, tarfile_mixed_contents.with_suffix("").with_suffix("")
    )
    extracted_tar = extract_tar(tarfile_without_suffix, temp_output_folder)
    assert extracted_tar == temp_output_folder / "dummy"
    assert (extracted_tar / "bar" / "foo.txt").is_file()
    with (extracted_tar / "bar" / "foo.txt").open("r") as open_file:
        assert "This is a test file." == open_file.read()


def test_extract_tar_more_than_two_extensions(tmp_path, tarfile_mixed_contents):
    temp_output_folder = tmp_path / "test_extract_tar_output"
    temp_output_folder.mkdir()
    suffixes = tarfile_mixed_contents.suffixes
    new_suffixes = [".bar", ".foo"] + suffixes
    tarfile_without_suffix = tarfile_mixed_contents.with_suffix("").with_suffix("")
    new_tarfile = tarfile_without_suffix
    for suffix in new_suffixes:
        new_tarfile = new_tarfile.with_suffix(new_tarfile.suffix + suffix)
    tarfile_without_suffix = shutil.move(tarfile_mixed_contents, new_tarfile)
    extracted_tar = extract_tar(new_tarfile, temp_output_folder)
    assert extracted_tar == temp_output_folder / "dummy.bar.foo"
    assert (extracted_tar / "bar" / "foo.txt").is_file()
    with (extracted_tar / "bar" / "foo.txt").open("r") as open_file:
        assert "This is a test file." == open_file.read()


def test_extract_tarfile_non_existant_file_raises(tmp_path):
    msg = r"nonexistent does not exist or is not a file\."
    with pytest.raises(FileNotFoundError, match=msg):
        extract_tar(Path("nonexistent"), str(tmp_path))


def test_extract_tarfile_not_a_tarfile_raises(tmp_path):
    msg = r"^.*foo.txt is not a tarfile\."
    tmp_file = tmp_path / "foo.txt"
    tmp_file.touch()
    with pytest.raises(ValueError, match=msg):
        extract_tar(tmp_file, str(tmp_path))


def test_extract_tarfile_nonexistant_output_directory_raises(
    tmp_path, tarfile_mixed_contents
):
    temp_output_folder = tmp_path / "nonexistant"
    msg = r"^Directory .*nonexistant does not exist or is not a directory."
    with pytest.raises(FileNotFoundError, match=msg):
        extract_tar(tarfile_mixed_contents, temp_output_folder)


def test_extract_tarfile_output_directory_contains_content_raises(
    tmp_path, tarfile_mixed_contents
):
    temp_output_folder = tmp_path / "already_contains_dummy"
    temp_output_folder.mkdir()
    (temp_output_folder / "dummy").mkdir()
    msg = r"^Tarfile would have been unpacked to .*already_contains_dummy/dummy, but a file or directory already exists at this location\."
    with pytest.raises(FileExistsError, match=msg):
        extract_tar(tarfile_mixed_contents, temp_output_folder)
