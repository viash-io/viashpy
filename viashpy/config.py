from __future__ import annotations
import yaml
from pathlib import Path


def read_viash_config(config_path: str | Path) -> dict:
    with open(config_path, "r") as open_config_file:
        config = yaml.safe_load(open_config_file)
    if not config:
        raise ValueError("The config file was empty.")
    if not isinstance(config, dict):
        raise ValueError(
            "Expected viash config to contain a map. "
            "Please make sure that providing a valid "
            "viash config yaml."
        )
    return config
