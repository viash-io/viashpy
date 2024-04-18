from __future__ import annotations
from subprocess import check_output, STDOUT, DEVNULL, PIPE, CalledProcessError
from pathlib import Path
from typing import Any
from .types import Engine, Platform
import logging
import re

logger = logging.getLogger(__name__)


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


def _format_cpu_and_memory(cpus, memory, arg_prefix="---"):
    result = []
    if cpus:
        # Must be a string because subprocess.check_output
        # only works with strings.
        result += [f"{arg_prefix}cpus", str(cpus)]
    if memory:
        assert any(
            [memory.endswith(suffix) for suffix in tobytesconverter.AVAILABLE_UNITS()]
        ), (
            "The memory specifier must have one of the following suffixes: "
            f"{','.join(tobytesconverter.AVAILABLE_UNITS())}"
        )
        result += [f"{arg_prefix}memory", memory]
    return result


def _get_viash_version(viash_executable):
    try:
        version_string = check_output([viash_executable, "--version"]).decode().strip()
        version_pattern = re.compile(
            r"^viash ([0-9]+.[0-9]+.[0-9]+).* \(c\) [0-9]{4} Data Intuitive$"
        )
        version_match = re.fullmatch(version_pattern, version_string)
        if not version_match:
            raise ValueError(
                "Could not parse the version information as output by viash."
            )
        return tuple(map(int, (version_match.group(1).split("."))))
    except CalledProcessError as e:
        logger.error(
            "Could not determine the viash version. "
            "Please make sure that viash is in your PATH "
            "or that you overwrite the 'viash_executable' fixture "
            "to return the correct location of the viash binairy."
        )
        raise e


def _check_platform_or_engine(
    viash_version: tuple[int, int, int],
    engine: Engine | None = None,
    platform: Platform | None = None,
):
    major_viash_version, minor_viash_version, _ = viash_version
    if platform is None and engine is None:
        # Use an appropriate default for the viash version
        if major_viash_version == 0 and minor_viash_version < 9:
            return "platform", "docker"
        else:
            return "engine", "docker"
    if platform and engine:
        raise ValueError("Cannot pass both an 'engine' and a 'plaform'.")
    if major_viash_version == 0 and minor_viash_version < 9:
        if engine:
            raise ValueError(
                f"Viash version {'.'.join(map(str, viash_version))} "
                "requires using 'platform' instead of 'engine'."
            )
        return "platform", platform
    else:
        if platform:
            raise ValueError(
                f"Viash version {'.'.join(map(str, viash_version))} "
                "requires using 'engine' instead of 'platform'."
            )
        return "engine", engine


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
    full_command = [executable_location] + args + _format_cpu_and_memory(cpus, memory)
    logger.debug("Running '%s'", " ".join(map(str, full_command)))
    return check_output(full_command, stderr=stderr, **popen_kwargs)


def viash_run(
    config: str | Path,
    args: list[str],
    *,
    cpus: int | None = None,
    memory: str | None = None,
    engine: Engine | None = None,
    platform: Platform | None = None,
    viash_location: str | Path = "viash",
    stderr: STDOUT | PIPE | DEVNULL | -1 | -2 | -3 = STDOUT,
    **popen_kwargs,
):
    config = Path(config)
    if not config.is_file():
        raise FileNotFoundError(f"{config} does not exist or is not a file.")
    args = ["--"] + args

    viash_version = _get_viash_version(viash_location)
    platform_or_engine, engine_or_platform_val = _check_platform_or_engine(
        viash_version, engine=engine, platform=platform
    )
    if engine_or_platform_val == "docker":
        build_args = [
            viash_location,
            "run",
            config,
            f"--{platform_or_engine}",
            engine_or_platform_val,
            "-c",
            f".{platform_or_engine}s[.type == 'docker'].target_tag := 'test'",
            "--",
            "---setup",
            "cachedbuild",
        ]
        logger.debug("Building docker image: %s", " ".join(map(str, build_args)))
        check_output(
            build_args, stderr=stderr, **popen_kwargs
        )  # CalledProcessError should be handled by caller
    full_command = (
        [
            viash_location,
            "run",
            config,
            f"--{platform_or_engine}",
            engine_or_platform_val,
            "-c",
            f".{platform_or_engine}s[.type == 'docker'].target_tag := 'test'",
        ]
        + _format_cpu_and_memory(cpus, memory, "--")
        + args
    )
    logger.debug("Running '%s'", " ".join(map(str, full_command)))
    return check_output(full_command, stderr=stderr, **popen_kwargs)
