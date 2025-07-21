import json
import os
from datetime import datetime
from .models import Slide

class SlideStore:
    # Path to the JSON file that defines the slides
    SLIDE_FILE = "slides.json"

    # In-memory list of loaded Slide objects
    _slides = []

    # Last modification time of the JSON file (used to detect changes)
    _last_modified_time = 0

    @classmethod
    def _load_slides(cls):
        # Internal method that loads the slides from the JSON file.
        # Only called when the file has changed or when forced.
        try:
            with open(cls.SLIDE_FILE, "r") as file:
                raw_data = json.load(file)
            cls._slides = []

            for item in raw_data:
                try:
                    # Convert start/end strings to datetime if present
                    start_time = datetime.fromisoformat(item["start"]) if item.get("start") else None
                    end_time = datetime.fromisoformat(item["end"]) if item.get("end") else None

                    slide = Slide(
                        source=item["source"],
                        duration=item["duration"],
                        start=start_time,
                        end=end_time
                    )
                    cls._slides.append(slide)
                except Exception as error:
                    print(f"Failed to load slide: {item} ({error})")

        except Exception as error:
            print(f"Error reading slide file: {error}")
            cls._slides = []

    @classmethod
    def get_active_slides(cls):
        # Returns a list of currently active slides.
        # Automatically reloads the slide file if it has been modified.
        try:
            current_mtime = os.path.getmtime(cls.SLIDE_FILE)

            if current_mtime != cls._last_modified_time:
                cls._last_modified_time = current_mtime
                cls._load_slides()

        except FileNotFoundError:
            cls._slides = []

        # Only return slides where the current time is between start and end
        return [slide for slide in cls._slides if slide.is_active()]

    @classmethod
    def force_reload(cls):
        # Forces the next call to get_active_slides() to reload the slide file,
        # even if the file hasn't been modified.
        cls._last_modified_time = 0

    @classmethod
    def add_slide(cls, slide_data):
        # Load current slide list from file
        try:
            with open(cls.SLIDE_FILE, "r") as file:
                current_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            current_data = []

        # Append the new slide
        current_data.append({
            "source": slide_data["source"],
            "duration": slide_data["duration"],
            "start": slide_data["start"],
            "end": slide_data["end"]
        })

        # Save back to file
        try:
            with open(cls.SLIDE_FILE, "w") as file:
                json.dump(current_data, file, indent=4)
            cls.force_reload()
        except Exception as e:
            print(f"Failed to save slide: {e}")
