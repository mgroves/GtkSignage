"""
Slide Store Module

This module provides functionality for managing slides in the GTK Signage application.
It handles loading, saving, and filtering slides based on their active status.
The slides are stored in a JSON file and accessed through the SlideStore class.
"""
import json
import os
from datetime import datetime
from .models import Slide
from .jsonfile import JSONFileHandler

class SlideStore:
    """
    A static utility class for managing slides.
    
    This class provides methods for loading, saving, and filtering slides.
    It maintains a cache of slides and monitors the slide file for changes.
    All methods are class methods as this is designed as a static utility class.
    """
    SLIDE_FILE = "slides.json"
    _slides = []
    _last_modified_time = 0
    _file_handler = JSONFileHandler(SLIDE_FILE)

    @classmethod
    def _load_slides(cls):
        """
        Load slides from the JSON file into memory.
        
        This private method reads the slide data from the JSON file,
        converts it to Slide objects, and stores them in the _slides class variable.
        
        If any errors occur during loading or parsing, the _slides list will be empty.
        """
        try:
            raw_data = cls._file_handler.load()
            cls._slides = []
            for item in raw_data:
                try:
                    start_time = datetime.fromisoformat(item["start"]) if item.get("start") else None
                    end_time = datetime.fromisoformat(item["end"]) if item.get("end") else None
                    slide = Slide(
                        source=item["source"],
                        duration=item["duration"],
                        start=start_time,
                        end=end_time,
                        hide=item.get("hide", False)
                    )
                    cls._slides.append(slide)
                except Exception:
                    pass
        except Exception:
            cls._slides = []

    @classmethod
    def get_active_slides(cls):
        """
        Get all currently active slides.
        
        This method checks if the slides file has been modified since the last load,
        reloads the slides if necessary, and returns only the active slides.
        
        Returns:
            list: A list of Slide objects that are currently active.
        """
        try:
            current_mtime = os.path.getmtime(cls.SLIDE_FILE)
            if current_mtime != cls._last_modified_time:
                cls._last_modified_time = current_mtime
                cls._load_slides()
        except FileNotFoundError:
            cls._slides = []
        return [slide for slide in cls._slides if slide.is_active()]

    @classmethod
    def force_reload(cls):
        """
        Force a reload of slides on the next access.
        
        This method resets the last modified time to ensure that the slides
        will be reloaded from the file the next time they are accessed.
        """
        cls._last_modified_time = 0

    @classmethod
    def add_slide(cls, slide_data):
        """
        Add a new slide to the store.
        
        Args:
            slide_data (dict): A dictionary containing the slide data.
                Must include 'source' and 'duration' keys.
                May optionally include 'start', 'end', and 'hide' keys.
                
        Raises:
            ValueError: If any required fields are missing.
            
        Note:
            This method loads the current slides from the file,
            adds the new slide, and saves the updated list back to the file.
        """
        required_fields = ["source", "duration"]
        for key in required_fields:
            if key not in slide_data:
                raise ValueError(f"Missing required field: {key}")

        try:
            current_data = cls._file_handler.load()
        except Exception:
            current_data = []

        current_data.append({
            "source": slide_data["source"],
            "duration": slide_data["duration"],
            "start": slide_data.get("start"),
            "end": slide_data.get("end"),
            "hide": slide_data.get("hide", False)
        })

        try:
            cls._file_handler.save(current_data)
            cls.force_reload()
        except Exception:
            pass

    @classmethod
    def save_slides(cls, slides):
        """
        Save a list of slides to the file.
        
        This method converts the Slide objects to dictionaries and saves them to the file.
        It then forces a reload to ensure the in-memory slides are up-to-date.
        
        Args:
            slides (list): A list of Slide objects to save.
        """
        data = []
        for s in slides:
            data.append({
                "source": s.source,
                "duration": s.duration,
                "start": s.start.isoformat() if s.start else None,
                "end": s.end.isoformat() if s.end else None,
                "hide": s.hide
            })
        cls._file_handler.save(data)
        cls.force_reload()

    @classmethod
    def get_all_slides(cls):
        """
        Get all slides, regardless of their active status.
        
        This method loads the slides from the file if necessary and returns all of them.
        
        Returns:
            list: A list of all Slide objects.
        """
        cls._load_slides()
        return cls._slides
