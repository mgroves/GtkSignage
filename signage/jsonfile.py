# jsonfile.py
import json
from filelock import FileLock
from pathlib import Path

class JSONFileHandler:
    def __init__(self, filename):
        self.file_path = Path(filename)
        self.lock = FileLock(f"{filename}.lock")

    def load(self):
        with self.lock:
            if not self.file_path.exists():
                return []
            with self.file_path.open("r", encoding="utf-8") as file:
                return json.load(file)

    def save(self, data):
        with self.lock:
            with self.file_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
