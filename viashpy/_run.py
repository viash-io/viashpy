from __future__ import annotations
from subprocess import check_output, STDOUT, DEVNULL, PIPE
from pathlib import Path
from typing import Any


class ToBytesConverter:
    # These need to be defined in order from smallest to largest!
    _AVAILABLE_UNITS = {
        "B": "B",
        "KB": "B",
        "MB": "KB",
        "GB": "MB",
        "TB": "GB",
        "PB": "TB",
    }

    def __call__(self, val: float | int, unit: str) -> Any:
        if unit == "B":
            return val
        return self(val * 1024, self._AVAILABLE_UNITS[unit])

    @classmethod
    def AVAILABLE_UNITS(cls) -> tuple:
        return tuple(cls._AVAILABLE_UNITS.keys())


tobytesconverter = ToBytesConverter()


def _add_cpu_and_memory(args, cpus, memory, arg_prefix):
    if cpus:
        # Must be a string because subprocess.check_output
        # only works with strings.
        args += [f"{arg_prefix}cpus", str(cpus)]
    if memory:
        assert any(
            [memory.endswith(suffix) for suffix in tobytesconverter.AVAILABLE_UNITS()]
        ), (
            "The memory specifier must have one of the following suffixes: "
            f"{','.join(tobytesconverter.AVAILABLE_UNITS())}"
        )
        args += [f"{arg_prefix}memory", memory]
    return args


def run_build_component(
    executable_location: str | Path,
    args: list[str],
    *,
    cpus: int | None = None,
    memory: str | None,
    stderr: STDOUT | PIPE | DEVNULL | -1 | -2 | -3 = STDOUT,
    **popen_kwargs,
):
    executable_location = Path(executable_location)
    if not executable_location.is_file():
        raise FileNotFoundError(
            f"{executable_location} does not exist or is not a file."
        )
    return check_output(
        [executable_location] + _add_cpu_and_memory(args, cpus, memory, "---"),
        stderr=stderr,
        **popen_kwargs,
    )


def viash_run(
    config: str | Path,
    args: list[str],
    *,
    cpus: int | None = None,
    memory: str | None = None,
    viash_location: str | Path = "viash",
    stderr: STDOUT | PIPE | DEVNULL | -1 | -2 | -3 = STDOUT,
    **popen_kwargs,
):
    config = Path(config)
    if not config.is_file():
        raise FileNotFoundError(f"{config} does not exist or is not a file.")
    return check_output(
        _add_cpu_and_memory([viash_location, "run", config], cpus, memory, "--")
        + ["--"]
        + args,
        stderr=stderr,
        **popen_kwargs,
    )
