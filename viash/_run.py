from __future__ import annotations
import os
from subprocess import check_output, STDOUT, DEVNULL, PIPE
from pathlib import Path


def run_build_component(
    executable_location: str | Path,
    args: list[str],
    *,
    stderr: STDOUT | PIPE | DEVNULL | -1 | -2 | -3 = STDOUT,
    **popen_kwargs,
):
    executable_location = Path(executable_location)
    if not executable_location.is_file():
        raise ValueError(f"{executable_location} does not exist or is not a file.")
    if not os.access(executable_location, os.X_OK):
        raise PermissionError(f"{executable_location} is not executable.")
    return check_output([executable_location] + args, stderr=stderr, **popen_kwargs)
