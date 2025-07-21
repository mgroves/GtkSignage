import json
import os
from datetime import datetime
from .models import Slide

class SlideStore:
    SLIDE_FILE = "slides.json"
    _slides = []
    _last_mtime = 0

    @classmethod
    def _load_slides(cls):
        try:
            with open(cls.SLIDE_FILE, "r") as f:
                data = json.load(f)
            cls._slides = []
            for item in data:
                try:
                    slide = Slide(
                        item["source"],
                        item["duration"],
                        datetime.fromisoformat(item["start"]) if item.get("start") else None,
                        datetime.fromisoformat(item["end"]) if item.get("end") else None
                    )
                    cls._slides.append(slide)
                except Exception as e:
                    print(f"Failed to load slide: {item} ({e})")
        except Exception as e:
            print(f"Error reading slide file: {e}")
            cls._slides = []

    @classmethod
    def get_active_slides(cls):
        try:
            mtime = os.path.getmtime(cls.SLIDE_FILE)
            if mtime != cls._last_mtime:
                cls._last_mtime = mtime
                cls._load_slides()
        except FileNotFoundError:
            cls._slides = []

        return [s for s in cls._slides if s.is_active()]

    @classmethod
    def force_reload(cls):
        cls._last_mtime = 0
