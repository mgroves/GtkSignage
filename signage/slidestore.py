# slidestore.py
import json
import os
from datetime import datetime
from .models import Slide
from .jsonfile import JSONFileHandler

class SlideStore:
    SLIDE_FILE = "slides.json"
    _slides = []
    _last_modified_time = 0
    _file_handler = JSONFileHandler(SLIDE_FILE)

    @classmethod
    def _load_slides(cls):
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
        cls._last_modified_time = 0

    @classmethod
    def add_slide(cls, slide_data):
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
        cls._load_slides()
        return cls._slides
