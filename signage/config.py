from __future__ import annotations

import configparser
import os
from pathlib import Path
from functools import lru_cache
from datetime import time as dtime

APP_ID = "com.mgroves.GtkSignage"


# ------------------------------------------------------------
# Config file location
# ------------------------------------------------------------

def get_config_path() -> Path:
    """
    Returns the absolute path to the config.ini file.

    Uses:
      - $XDG_CONFIG_HOME/com.mgroves.GtkSignage/config.ini
      - or ~/.config/com.mgroves.GtkSignage/config.ini
    """
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / APP_ID / "config.ini"


# ------------------------------------------------------------
# Load & cache config
# ------------------------------------------------------------

@lru_cache(maxsize=1)
def load_config() -> configparser.ConfigParser:
    """
    Load and cache the configuration file.

    The config is cached for the lifetime of the process.
    """
    config_path = get_config_path()

    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found:\n\n"
            f"  {config_path}\n\n"
            f"Create it before running GtkSignage."
        )

    parser = configparser.ConfigParser()
    parser.read(config_path)
    return parser


# ------------------------------------------------------------
# Typed accessors
# ------------------------------------------------------------

def get_str(section: str, key: str, default: str | None = None) -> str | None:
    cfg = load_config()
    try:
        return cfg.get(section, key)
    except (configparser.NoSectionError, configparser.NoOptionError):
        return default


def get_int(section: str, key: str, default: int) -> int:
    cfg = load_config()
    try:
        return cfg.getint(section, key)
    except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
        return default


def get_bool(section: str, key: str, default: bool = False) -> bool:
    cfg = load_config()
    try:
        return cfg.getboolean(section, key)
    except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
        return default


def get_path(section: str, key: str, default: str | Path) -> Path:
    """
    Returns a Path, expanding ~ and environment variables.

    If the value is relative, it is resolved relative to the config file.
    """
    raw = get_str(section, key, None)
    if raw is None:
        raw = str(default)

    raw = os.path.expandvars(os.path.expanduser(raw))
    path = Path(raw)

    if not path.is_absolute():
        path = get_config_path().parent / path

    return path.resolve()

def get_data_dir() -> Path:
    """
    Return the base data directory for persistent app files.
    """
    config = load_config()
    path = config.get("paths", "data_dir", fallback="data")
    p = Path(path).expanduser()
    p.mkdir(parents=True, exist_ok=True)
    return p

def get_time(section: str, key: str, default: str) -> dtime:
    """
    Read a HH:MM time value from config and return a datetime.time.
    """
    config = load_config()
    value = config.get(section, key, fallback=default)

    try:
        return dtime.fromisoformat(value.strip())
    except Exception as exc:
        raise ValueError(
            f"Invalid time value for [{section}].{key}: {value}"
        ) from exc

__all__ = [
    "load_config",
    "get_bool",
    "get_int",
    "get_path",
    "get_time",
    "get_data_dir",
]