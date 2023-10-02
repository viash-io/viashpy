from __future__ import annotations
from subprocess import check_output, STDOUT, DEVNULL, PIPE
from pathlib import Path


def _add_cpu_and_memory(args, cpus, memory_gb, arg_prefix):
    if cpus:
        # Must be a string because subprocess.check_output
        # only works with strings.
        args += [f"{arg_prefix}cpus", str(cpus)]
    if memory_gb:
        args += [f"{arg_prefix}memory", f"{memory_gb}GB"]
    return args


def run_build_component(
    executable_location: str | Path,
    args: list[str],
    *,
    cpus: int | None = None,
    memory_gb: str | None,
    stderr: STDOUT | PIPE | DEVNULL | -1 | -2 | -3 = STDOUT,
    **popen_kwargs,
):
    executable_location = Path(executable_location)
    if not executable_location.is_file():
        raise FileNotFoundError(
            f"{executable_location} does not exist or is not a file."
        )
    return check_output(
        [executable_location] + _add_cpu_and_memory(args, cpus, memory_gb, "---"),
        stderr=stderr,
        **popen_kwargs,
    )


def viash_run(
    config: str | Path,
    args: list[str],
    *,
    cpus: int | None = None,
    memory_gb: str | None = None,
    viash_location: str | Path = "viash",
    stderr: STDOUT | PIPE | DEVNULL | -1 | -2 | -3 = STDOUT,
    **popen_kwargs,
):
    config = Path(config)
    if not config.is_file():
        raise FileNotFoundError(f"{config} does not exist or is not a file.")
    return check_output(
        [viash_location, "run", config, "--"]
        + _add_cpu_and_memory(args, cpus, memory_gb, "--"),
        stderr=stderr,
        **popen_kwargs,
    )
