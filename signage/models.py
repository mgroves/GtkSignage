"""
Models Module

Data models for the GTK Signage application.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class Slide:
    """
    Represents a single signage slide.
    """

    def __init__(
        self,
        source: str,
        duration: int,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        hide: bool = False,
    ):
        # ---- Validate source -------------------------------------
        if not isinstance(source, str) or not source.strip():
            raise ValueError("source must be a non-empty string")

        # ---- Validate duration -----------------------------------
        try:
            duration = int(duration)
        except (TypeError, ValueError):
            raise TypeError("duration must be an integer")

        if duration <= 0:
            raise ValueError("duration must be positive")

        # ---- Validate start / end --------------------------------
        if start is not None and not isinstance(start, datetime):
            raise TypeError("start must be a datetime or None")

        if end is not None and not isinstance(end, datetime):
            raise TypeError("end must be a datetime or None")

        if start and end and start >= end:
            raise ValueError("start must be before end")

        # ---- Validate hide ---------------------------------------
        if not isinstance(hide, bool):
            raise TypeError("hide must be boolean")

        self.source: str = source
        self.duration: int = duration
        self.start: Optional[datetime] = start
        self.end: Optional[datetime] = end
        self.hide: bool = hide

    # ------------------------------------------------------------
    # State
    # ------------------------------------------------------------

    def is_active(self, now: Optional[datetime] = None) -> bool:
        """
        Determine whether this slide should currently be displayed.
        """
        if self.hide:
            return False

        now = now or datetime.now()

        if self.start and now < self.start:
            return False

        if self.end and now > self.end:
            return False

        return True

    # ------------------------------------------------------------
    # Debug / display
    # ------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Slide(source={self.source!r}, "
            f"duration={self.duration}, "
            f"start={self.start}, "
            f"end={self.end}, "
            f"hide={self.hide})"
        )