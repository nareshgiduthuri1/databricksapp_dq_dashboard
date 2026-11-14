"""
config_loader
=============
Central, cached YAML configuration loader for the STTM-to-Code pipeline.

This module replaces the previous ``.env`` / ``python-dotenv`` approach.
Every input/output path, directory, LLM model selection, target
platform, SQL dialect, and provider credential now lives in a single
``config.yaml`` (see ``config.example.yaml`` for the template).

Usage
-----
    from config_loader import get, get_section, load_config

    xml = get("io.input_xml_file")
    platform = get("generation.data_platform", "Databricks")
    gpt4o = get_section("providers.azure_openai_gpt4o")

The config file is resolved (in priority order) from:
    1. the ``APP_CONFIG_FILE`` environment variable, if set
    2. ``config.yaml`` next to this module (project root)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent
_DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"

_CONFIG_CACHE: Optional[Dict[str, Any]] = None
_LOADED_PATH: Optional[Path] = None


def config_path() -> Path:
    """Resolve the active config file path (APP_CONFIG_FILE wins)."""
    override = os.getenv("APP_CONFIG_FILE")
    return Path(override).expanduser() if override else _DEFAULT_CONFIG_PATH


def load_config(force_reload: bool = False) -> Dict[str, Any]:
    """
    Load and cache the YAML config. Raises ``FileNotFoundError`` with a
    helpful message if the file is missing.
    """
    global _CONFIG_CACHE, _LOADED_PATH

    if _CONFIG_CACHE is not None and not force_reload:
        return _CONFIG_CACHE

    path = config_path()
    if not path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {path}\n"
            "Copy 'config.example.yaml' to 'config.yaml' and fill in your "
            "values, or set APP_CONFIG_FILE to point at your config."
        )

    with open(path, "r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp) or {}

    _CONFIG_CACHE = data
    _LOADED_PATH = path
    return data


def get(dotted_key: str, default: Any = None) -> Any:
    """
    Fetch a value via a dot-separated path, e.g. ``get('llm.default_model')``.
    Returns ``default`` if any segment is missing.
    """
    node: Any = load_config()
    for key in dotted_key.split("."):
        if isinstance(node, dict) and key in node:
            node = node[key]
        else:
            return default
    return node


def get_section(dotted_key: str) -> Dict[str, Any]:
    """Return a config sub-section as a dict (empty dict if absent)."""
    section = get(dotted_key, {})
    return section if isinstance(section, dict) else {}
