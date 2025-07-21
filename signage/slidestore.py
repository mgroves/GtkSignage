import json
import os
from datetime import datetime
from signage.models import Slide

class SlideStore:
    def __init__(self, path="slides.json"):
        self.path = path

    def load_slides(self):
        if not os.path.exists(self.path):
            return []

        with open(self.path, "r") as f:
            data = json.load(f)

        slides = []
        for entry in data:
            try:
                slides.append(Slide(
                    source=entry["source"],
                    duration=entry["duration"],
                    start=datetime.fromisoformat(entry["start"]) if "start" in entry else None,
                    end=datetime.fromisoformat(entry["end"]) if "end" in entry else None
                ))
            except Exception as e:
                print(f"Failed to load slide: {entry} ({e})")

        return slides
