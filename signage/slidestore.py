"""
Slide Store Module

This module provides functionality for managing slides in the GTK Signage application.
It handles loading, saving, and filtering slides based on their active status.
The slides are stored in a JSON file and accessed through the SlideStore class.
"""
import os
import json
import logging
from datetime import datetime

from .jsonfile import JSONFileHandler
from .models import Slide

# Get logger for this module
logger = logging.getLogger(__name__)

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
        logger.debug(f"Loading slides from {cls.SLIDE_FILE}")
        try:
            raw_data = cls._file_handler.load()
            logger.debug(f"Loaded {len(raw_data)} raw slide entries")
            
            cls._slides = []
            for i, item in enumerate(raw_data):
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
                    logger.debug(f"Processed slide {i+1}/{len(raw_data)}: {slide.source}")
                except (KeyError, ValueError) as e:
                    logger.error(f"Error parsing slide data at index {i}: {e}")
                    logger.debug(f"Problematic slide data: {item}")
            
            logger.info(f"Successfully loaded {len(cls._slides)} slides")
        except (IOError, ValueError, json.JSONDecodeError) as e:
            logger.error(f"Error loading slides file: {e}")
            cls._slides = []
            logger.info("Initialized with empty slide list due to error")

    @classmethod
    def get_active_slides(cls):
        """
        Get all currently active slides.
        
        This method checks if the slides file has been modified since the last load,
        reloads the slides if necessary, and returns only the active slides.
        
        Returns:
            list: A list of Slide objects that are currently active.
        """
        logger.debug("Checking for active slides")
        try:
            current_mtime = os.path.getmtime(cls.SLIDE_FILE)
            if current_mtime != cls._last_modified_time:
                logger.info(f"Slide file modified (mtime: {current_mtime}, last: {cls._last_modified_time})")
                cls._last_modified_time = current_mtime
                cls._load_slides()
            else:
                logger.debug("Slide file unchanged since last check")
        except FileNotFoundError:
            logger.warning(f"Slide file not found: {cls.SLIDE_FILE}")
            cls._slides = []
        
        active_slides = [slide for slide in cls._slides if slide.is_active()]
        logger.debug(f"Found {len(active_slides)}/{len(cls._slides)} active slides")
        
        if not active_slides and cls._slides:
            logger.info("No active slides found despite having slides loaded")
            
        return active_slides

    @classmethod
    def force_reload(cls):
        """
        Force a reload of slides on the next access.
        
        This method resets the last modified time to ensure that the slides
        will be reloaded from the file the next time they are accessed.
        """
        logger.debug("Forcing reload of slides on next access")
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
            ValueError: If any required fields are missing or invalid.
            TypeError: If any fields have incorrect types.
            
        Note:
            This method loads the current slides from the file,
            adds the new slide, and saves the updated list back to the file.
        """
        logger.info(f"Adding new slide with source: {slide_data.get('source', 'unknown')}")
        logger.debug(f"Full slide data: {slide_data}")
        
        # Validate required fields
        required_fields = ["source", "duration"]
        for key in required_fields:
            if key not in slide_data:
                logger.error(f"Cannot add slide: Missing required field: {key}")
                raise ValueError(f"Missing required field: {key}")
        
        # Validate source
        source = slide_data["source"]
        if not isinstance(source, str):
            logger.error("Source must be a string")
            raise TypeError("Source must be a string")
        if not source.strip():
            logger.error("Source cannot be empty")
            raise ValueError("Source cannot be empty")
        
        # Validate duration
        try:
            duration = int(slide_data["duration"])
            if duration <= 0:
                logger.error("Duration must be positive")
                raise ValueError("Duration must be positive")
        except (ValueError, TypeError):
            logger.error("Duration must be an integer")
            raise TypeError("Duration must be an integer")
        
        # Validate start and end times
        start = slide_data.get("start")
        end = slide_data.get("end")
        
        if start:
            try:
                if isinstance(start, str):
                    start = datetime.fromisoformat(start)
            except ValueError:
                logger.error("Invalid start time format")
                raise ValueError("Invalid start time format")
        
        if end:
            try:
                if isinstance(end, str):
                    end = datetime.fromisoformat(end)
            except ValueError:
                logger.error("Invalid end time format")
                raise ValueError("Invalid end time format")
        
        if start and end and start >= end:
            logger.error("Start time must be before end time")
            raise ValueError("Start time must be before end time")
        
        # Validate hide flag
        hide = slide_data.get("hide", False)
        if not isinstance(hide, bool):
            try:
                # Convert to boolean if it's a string like "true" or "false"
                if isinstance(hide, str):
                    hide = hide.lower() in ("true", "yes", "1", "t", "y")
                else:
                    hide = bool(hide)
            except:
                logger.error("Hide flag must be a boolean")
                raise TypeError("Hide flag must be a boolean")

        try:
            logger.debug("Loading current slides data")
            current_data = cls._file_handler.load()
            logger.debug(f"Loaded {len(current_data)} existing slides")
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Error loading slides for adding new slide: {e}")
            logger.info("Initializing with empty slide list due to error")
            current_data = []

        # Prepare the new slide data
        new_slide = {
            "source": source,
            "duration": duration,
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
            "hide": hide
        }
        
        logger.debug(f"Prepared new slide data: {new_slide}")
        current_data.append(new_slide)

        try:
            logger.debug(f"Saving updated slides data with {len(current_data)} slides")
            cls._file_handler.save(current_data)
            logger.info(f"Successfully added new slide, total slides: {len(current_data)}")
            cls.force_reload()
        except (IOError, PermissionError) as e:
            logger.error(f"Error saving slides: {e}")
            raise

    @classmethod
    def save_slides(cls, slides):
        """
        Save a list of slides to the file.
        
        This method converts the Slide objects to dictionaries and saves them to the file.
        It then forces a reload to ensure the in-memory slides are up-to-date.
        
        Args:
            slides (list): A list of Slide objects to save.
        """
        logger.info(f"Saving {len(slides)} slides to file")
        
        data = []
        for i, s in enumerate(slides):
            slide_dict = {
                "source": s.source,
                "duration": s.duration,
                "start": s.start.isoformat() if s.start else None,
                "end": s.end.isoformat() if s.end else None,
                "hide": s.hide
            }
            data.append(slide_dict)
            logger.debug(f"Prepared slide {i+1}/{len(slides)} for saving: {s.source}")
        
        try:
            logger.debug(f"Writing {len(data)} slides to {cls.SLIDE_FILE}")
            cls._file_handler.save(data)
            logger.info(f"Successfully saved {len(data)} slides")
            cls.force_reload()
        except Exception as e:
            logger.error(f"Error saving slides to file: {e}")
            raise

    @classmethod
    def get_all_slides(cls):
        """
        Get all slides, regardless of their active status.
        
        This method loads the slides from the file if necessary and returns all of them.
        
        Returns:
            list: A list of all Slide objects.
        """
        logger.debug("Getting all slides, regardless of active status")
        cls._load_slides()
        logger.debug(f"Returning {len(cls._slides)} total slides")
        return cls._slides
