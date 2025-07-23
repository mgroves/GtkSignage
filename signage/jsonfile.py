# jsonfile.py
import json
from filelock import FileLock
from pathlib import Path
from typing import Any, Dict, List, Union

class JSONFileHandler:
    def __init__(self, filename: str) -> None:
        self.file_path: Path = Path(filename)
        self.lock: FileLock = FileLock(f"{filename}.lock")

    def load(self) -> List[Dict[str, Any]]:
        with self.lock:
            if not self.file_path.exists():
                return []
            with self.file_path.open("r", encoding="utf-8") as file:
                return json.load(file)

    def save(self, data: List[Dict[str, Any]]) -> None:
        with self.lock:
            with self.file_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
