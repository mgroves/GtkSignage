"""
Models Module

This module defines the data models used in the GTK Signage application.
It contains the Slide class which represents a single slide in the signage system.
"""
from datetime import datetime

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
        """
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
        if self.hide:
            return False

        now = datetime.now()

        if not self.start and not self.end:
            return True

        if not self.start and self.end:
            return now <= self.end

        if self.start and not self.end:
            return now >= self.start

        if self.start and self.end:
            return self.start <= now <= self.end

        return False

