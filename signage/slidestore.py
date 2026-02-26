"""
Slide Store Module

Manages loading, saving, and filtering slides for the GTK Signage application.
Slides are stored in a JSON file whose location is defined via INI config.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import List

from signage.config import load_config
from signage.jsonfile import JSONFileHandler
from signage.models import Slide


logger = logging.getLogger(__name__)
config = load_config()


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

SLIDE_FILE = config.get("slides", "file", fallback="slides.json")

# ------------------------------------------------------------
# Slide Store
# ------------------------------------------------------------

class SlideStore:
    """
    Static utility class for managing slides.

    Uses a JSON file as backing storage and keeps an in-memory cache
    that reloads automatically when the file changes.
    """

    _slides: List[Slide] = []
    _last_mtime: float = 0.0
    _file_handler = JSONFileHandler(SLIDE_FILE)

    # --------------------------------------------------------

    @classmethod
    def _load_slides(cls) -> None:
        """
        Load slides from disk into memory.
        """
        logger.debug("Loading slides from %s", SLIDE_FILE)

        try:
            raw = cls._file_handler.load()
        except (IOError, json.JSONDecodeError) as exc:
            logger.error("Failed to load slides file: %s", exc)
            cls._slides = []
            return

        slides: List[Slide] = []

        for idx, item in enumerate(raw):
            try:
                start = (
                    datetime.fromisoformat(item["start"])
                    if item.get("start")
                    else None
                )
                end = (
                    datetime.fromisoformat(item["end"])
                    if item.get("end")
                    else None
                )

                slide = Slide(
                    source=item["source"],
                    duration=int(item["duration"]),
                    start=start,
                    end=end,
                    hide=bool(item.get("hide", False)),
                )
                slides.append(slide)

            except Exception as exc:
                logger.error(
                    "Invalid slide at index %d: %s", idx, exc
                )
                logger.debug("Slide data: %r", item)

        cls._slides = slides
        logger.info("Loaded %d slides", len(slides))

    # --------------------------------------------------------

    @classmethod
    def _reload_if_needed(cls) -> None:
        """
        Reload slides if the backing file has changed.
        """
        try:
            mtime = os.path.getmtime(SLIDE_FILE)
        except FileNotFoundError:
            if cls._slides:
                logger.warning("Slides file missing, clearing cache")
            cls._slides = []
            cls._last_mtime = 0
            return

        if mtime != cls._last_mtime:
            logger.info(
                "Slides file changed (mtime %s → %s)",
                cls._last_mtime,
                mtime,
            )
            cls._last_mtime = mtime
            cls._load_slides()

    # --------------------------------------------------------

    @classmethod
    def get_active_slides(cls) -> List[Slide]:
        """
        Return all currently active slides.
        """
        cls._reload_if_needed()

        active = [s for s in cls._slides if s.is_active()]
        logger.debug(
            "Active slides: %d / %d", len(active), len(cls._slides)
        )
        return active

    # --------------------------------------------------------

    @classmethod
    def get_all_slides(cls) -> List[Slide]:
        """
        Return all slides regardless of active status.
        """
        cls._reload_if_needed()
        return list(cls._slides)

    # --------------------------------------------------------

    @classmethod
    def force_reload(cls) -> None:
        """
        Force reload on next access.
        """
        cls._last_mtime = 0

    # --------------------------------------------------------

    @classmethod
    def save_slides(cls, slides: List[Slide]) -> None:
        """
        Persist a list of Slide objects to disk.
        """
        data = []

        for s in slides:
            data.append(
                {
                    "source": s.source,
                    "duration": s.duration,
                    "start": s.start.isoformat() if s.start else None,
                    "end": s.end.isoformat() if s.end else None,
                    "hide": s.hide,
                }
            )

        cls._file_handler.save(data)
        logger.info("Saved %d slides", len(data))
        cls.force_reload()

    # --------------------------------------------------------

    @classmethod
    def add_slide(cls, slide_data: dict) -> None:
        """
        Add a single slide entry and persist immediately.
        """
        required = ("source", "duration")
        for key in required:
            if key not in slide_data:
                raise ValueError(f"Missing required field: {key}")

        source = str(slide_data["source"]).strip()
        if not source:
            raise ValueError("Source cannot be empty")

        duration = int(slide_data["duration"])
        if duration <= 0:
            raise ValueError("Duration must be positive")

        start = slide_data.get("start")
        end = slide_data.get("end")

        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        if isinstance(end, str):
            end = datetime.fromisoformat(end)

        if start and end and start >= end:
            raise ValueError("Start time must be before end time")

        hide = bool(slide_data.get("hide", False))

        try:
            existing = cls._file_handler.load()
        except Exception:
            existing = []

        existing.append(
            {
                "source": source,
                "duration": duration,
                "start": start.isoformat() if start else None,
                "end": end.isoformat() if end else None,
                "hide": hide,
            }
        )

        cls._file_handler.save(existing)
        logger.info("Added slide: %s", source)
        cls.force_reload()