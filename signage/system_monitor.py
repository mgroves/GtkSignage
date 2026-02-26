"""
System Monitor Module

Provides system resource metrics such as CPU, memory, disk, and temperature.
All behavior is driven by configuration and safe for Flatpak environments.
"""

from __future__ import annotations

import logging
import platform
from typing import Optional, Dict, Any

import psutil

from signage.config import load_config


logger = logging.getLogger(__name__)
config = load_config()


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

DISK_PATH = config.get("system", "disk_path", fallback="/")
ENABLE_TEMPERATURE = config.getboolean(
    "system", "enable_temperature", fallback=True
)


# ------------------------------------------------------------
# CPU
# ------------------------------------------------------------

def get_cpu_usage() -> Optional[float]:
    """
    Get current CPU usage percentage.

    Returns:
        float or None
    """
    try:
        return psutil.cpu_percent(interval=0.5)
    except Exception as exc:
        logger.error("CPU usage error: %s", exc)
        return None


# ------------------------------------------------------------
# Memory
# ------------------------------------------------------------

def get_memory_usage() -> Optional[Dict[str, Any]]:
    """
    Get memory usage statistics.

    Returns:
        dict or None
    """
    try:
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "percent": mem.percent,
        }
    except Exception as exc:
        logger.error("Memory usage error: %s", exc)
        return None


# ------------------------------------------------------------
# Disk
# ------------------------------------------------------------

def get_disk_usage() -> Optional[Dict[str, Any]]:
    """
    Get disk usage statistics for configured path.

    Returns:
        dict or None
    """
    try:
        disk = psutil.disk_usage(DISK_PATH)
        return {
            "path": DISK_PATH,
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
        }
    except Exception as exc:
        logger.error("Disk usage error (%s): %s", DISK_PATH, exc)
        return None


# ------------------------------------------------------------
# Temperature
# ------------------------------------------------------------

def get_temperature() -> Optional[float]:
    """
    Get CPU temperature in Celsius if available and enabled.

    Returns:
        float or None
    """
    if not ENABLE_TEMPERATURE:
        return None

    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return None

        # Prefer CPU-like sensors
        for name, entries in temps.items():
            lname = name.lower()
            if any(k in lname for k in ("cpu", "core", "package")):
                if entries:
                    return entries[0].current

        # Fallback to first available sensor
        first = next(iter(temps.values()), None)
        if first:
            return first[0].current

        return None
    except Exception as exc:
        logger.debug("Temperature unavailable: %s", exc)
        return None


# ------------------------------------------------------------
# System Info
# ------------------------------------------------------------

def get_system_info() -> Optional[Dict[str, Any]]:
    """
    Get basic system metadata.

    Returns:
        dict or None
    """
    try:
        return {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(),
            "boot_time": psutil.boot_time(),
        }
    except Exception as exc:
        logger.error("System info error: %s", exc)
        return None


# ------------------------------------------------------------
# Aggregate
# ------------------------------------------------------------

def get_all_stats() -> Dict[str, Any]:
    """
    Get all system statistics in one call.

    Returns:
        dict
    """
    return {
        "cpu": get_cpu_usage(),
        "memory": get_memory_usage(),
        "disk": get_disk_usage(),
        "temperature": get_temperature(),
        "system_info": get_system_info(),
    }