"""
JSON File Handler Module

Safe JSON read/write with file locking.
All files are stored in the configured data directory.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from filelock import FileLock

from signage.config import get_data_dir

logger = logging.getLogger(__name__)


class JSONFileHandler:
    """
    Handles JSON file operations with file locking.
    """

    def __init__(self, filename: str):
        """
        Args:
            filename: Filename only (no path). Stored under data dir.
        """
        if "/" in filename or "\\" in filename:
            raise ValueError("filename must not contain path separators")

        data_dir = get_data_dir()
        self.file_path: Path = data_dir / filename
        self.lock = FileLock(str(self.file_path) + ".lock")

    # ------------------------------------------------------------
    # Read
    # ------------------------------------------------------------

    def load(self) -> Any:
        """
        Load JSON data from disk.

        Returns:
            Parsed JSON data, or empty list if missing or invalid.
        """
        with self.lock:
            if not self.file_path.exists():
                logger.info("JSON file not found, returning empty list: %s", self.file_path)
                return []

            try:
                with self.file_path.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON in %s: %s", self.file_path, e)
                return []
            except Exception as e:
                logger.error("Error reading %s: %s", self.file_path, e)
                return []

    # ------------------------------------------------------------
    # Write
    # ------------------------------------------------------------

    def save(self, data: Any) -> None:
        """
        Save JSON data to disk.

        Raises on write failure.
        """
        with self.lock:
            try:
                self.file_path.parent.mkdir(parents=True, exist_ok=True)

                with self.file_path.open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            except Exception as e:
                logger.error("Error writing %s: %s", self.file_path, e)
                raise