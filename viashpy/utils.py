from __future__ import annotations
from pathlib import Path
import tarfile
import logging

logger = logging.Logger(__name__)


def _recursive_stem(path: Path):
    one_suffix_removed = path.with_suffix("")
    while path != one_suffix_removed:
        path = path.with_suffix("")
        one_suffix_removed = path.with_suffix("")
    return path


def extract_tar(pathname: Path | str, output_dir: Path | str):
    pathname, output_dir = Path(pathname), Path(output_dir)

    if not pathname.is_file():
        raise FileNotFoundError(f"{pathname} does not exist or is not a file.")

    if not tarfile.is_tarfile(pathname):
        raise ValueError(f"{pathname} is not a tarfile.")

    if not output_dir.is_dir():
        raise FileNotFoundError(
            f"Directory {output_dir} does not exist or is not a directory."
        )

    suffixes = pathname.suffixes
    last_two_suffixes = suffixes[max(-2, -len(suffixes)) :]

    new_suffixes = suffixes
    if ".tar" in last_two_suffixes:
        new_suffixes = (
            suffixes[: -len(last_two_suffixes)]
            + last_two_suffixes[: last_two_suffixes.index(".tar")]
        )

    unpacked_path = _recursive_stem(output_dir / pathname.name)
    for suffix in new_suffixes:
        unpacked_path = unpacked_path.with_suffix(unpacked_path.suffix + suffix)

    if unpacked_path.exists():
        raise FileExistsError(
            f"Tarfile would have been unpacked to {unpacked_path}, but a file or directory already exists at this location."
        )

    with tarfile.open(pathname, "r") as open_tar:
        members = open_tar.getmembers()
        root_dirs = [
            member
            for member in members
            if member.isdir() and member.name != "." and "/" not in member.name
        ]
        # if there is only one root_dir (and there are files in that directory)
        # strip that directory name from the destination folder
        if len(root_dirs) == 1:
            root_dir = root_dirs[0].name
            for mem in members:
                mem.path = Path(mem.path).relative_to(root_dir)
        members_to_move = [mem for mem in members if mem.path != Path(".")]
        open_tar.extractall(unpacked_path, members=members_to_move)
    return unpacked_path

# helper function for cheching whether something is a gzip
def is_gz_file(path: Path) -> bool:
    with open(path, "rb") as file:
        return file.read(2) == b"\x1f\x8b"

# if {par_value} is a Path, extract it to a temp_dir_path and return the resulting path
def extract_if_need_be(pathname: Path | str, output_dir: Path | str) -> Path:
    pathname, output_dir = Path(pathname), Path(output_dir)

    if pathname.is_file() and tarfile.is_tarfile(pathname):
        logger.info("Tar detected; extracting %s", pathname)
        return extract_tar(pathname, output_dir)

    elif pathname.is_file() and is_gz_file(pathname):
        # Remove extension (if it exists)
        extaction_file_name = Path(pathname.stem)
        unpacked_path = output_dir / extaction_file_name
        logger.info("Gzip detected; extracting %s", pathname)

        import gzip
        import shutil
        
        with gzip.open(pathname, "rb") as f_in:
            with open(unpacked_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        return unpacked_path

    else:
        return pathname