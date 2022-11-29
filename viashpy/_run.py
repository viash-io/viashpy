from __future__ import annotations
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
        raise FileNotFoundError(
            f"{executable_location} does not exist or is not a file."
        )
    return check_output([executable_location] + args, stderr=stderr, **popen_kwargs)


def viash_run(
    config: str | Path,
    args: list[str],
    *,
    viash_location: str | Path = "viash",
    stderr: STDOUT | PIPE | DEVNULL | -1 | -2 | -3 = STDOUT,
    **popen_kwargs,
):
    config = Path(config)
    if not config.is_file():
        raise FileNotFoundError(f"{config} does not exist or is not a file.")
    return check_output(
        [viash_location, "run", config, "--"] + args, stderr=stderr, **popen_kwargs
    )
