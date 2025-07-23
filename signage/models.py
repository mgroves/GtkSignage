"""
Models Module

This module defines the data models used in the GTK Signage application.
It contains the Slide class which represents a single slide in the signage system.
"""
import logging
from datetime import datetime

# Get logger for this module
logger = logging.getLogger(__name__)

class Slide:
    """
    A class representing a slide in the signage system.
    
    A slide has a source (URL or file path), duration, optional start and end times,
    and a flag to hide it from display.
    """
    def __init__(self, source, duration, start=None, end=None, hide=False):
        """
        Initialize a Slide instance.
        
        Args:
            source (str): URL or file path to the slide content.
            duration (int): Duration in seconds to display the slide.
            start (datetime, optional): Start time when the slide becomes active. Defaults to None.
            end (datetime, optional): End time when the slide becomes inactive. Defaults to None.
            hide (bool, optional): Flag to hide the slide regardless of timing. Defaults to False.
            
        Raises:
            ValueError: If any of the parameters are invalid.
            TypeError: If any of the parameters have incorrect types.
        """
        # Validate source
        if not isinstance(source, str):
            raise TypeError("Source must be a string")
        if not source.strip():
            raise ValueError("Source cannot be empty")
        
        # Validate duration
        if not isinstance(duration, int):
            try:
                duration = int(duration)
            except (ValueError, TypeError):
                raise TypeError("Duration must be an integer")
        if duration <= 0:
            raise ValueError("Duration must be positive")
            
        # Validate start and end times
        if start is not None and not isinstance(start, datetime):
            raise TypeError("Start time must be a datetime object")
        if end is not None and not isinstance(end, datetime):
            raise TypeError("End time must be a datetime object")
        if start and end and start >= end:
            raise ValueError("Start time must be before end time")
            
        # Validate hide flag
        if not isinstance(hide, bool):
            raise TypeError("Hide flag must be a boolean")
            
        self.source = source
        self.duration = duration
        self.start = start if start else None
        self.end = end if end else None
        self.hide = hide

    def is_active(self):
        """
        Determine if the slide is currently active and should be displayed.
        
        A slide is active if:
        - It is not hidden
        - The current time is within its start and end times (if specified)
        
        Returns:
            bool: True if the slide is active and should be displayed, False otherwise.
        """
        # Get a short identifier for the slide for logging
        slide_id = self.source.split('/')[-1] if '/' in self.source else self.source
        
        if self.hide:
            logger.debug(f"Slide '{slide_id}' is inactive: manually hidden")
            return False

        now = datetime.now()
        logger.debug(f"Checking if slide '{slide_id}' is active at {now.isoformat()}")

        # No time constraints
        if not self.start and not self.end:
            logger.debug(f"Slide '{slide_id}' is active: no time constraints")
            return True

        # Only end time constraint
        if not self.start and self.end:
            is_active = now <= self.end
            if is_active:
                logger.debug(f"Slide '{slide_id}' is active: current time is before end time {self.end.isoformat()}")
            else:
                logger.debug(f"Slide '{slide_id}' is inactive: current time is after end time {self.end.isoformat()}")
            return is_active

        # Only start time constraint
        if self.start and not self.end:
            is_active = now >= self.start
            if is_active:
                logger.debug(f"Slide '{slide_id}' is active: current time is after start time {self.start.isoformat()}")
            else:
                logger.debug(f"Slide '{slide_id}' is inactive: current time is before start time {self.start.isoformat()}")
            return is_active

        # Both start and end time constraints
        if self.start and self.end:
            is_active = self.start <= now <= self.end
            if is_active:
                logger.debug(f"Slide '{slide_id}' is active: current time is between start {self.start.isoformat()} and end {self.end.isoformat()}")
            else:
                if now < self.start:
                    logger.debug(f"Slide '{slide_id}' is inactive: current time is before start time {self.start.isoformat()}")
                else:
                    logger.debug(f"Slide '{slide_id}' is inactive: current time is after end time {self.end.isoformat()}")
            return is_active

        logger.warning(f"Slide '{slide_id}' reached unexpected condition in is_active()")
        return False

