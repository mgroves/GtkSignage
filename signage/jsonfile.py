"""
JSON File Handler Module

This module provides functionality for safely reading from and writing to JSON files
with file locking to prevent concurrent access issues.
"""
import json
from filelock import FileLock
from pathlib import Path

class JSONFileHandler:
    """
    A class for handling JSON file operations with file locking.
    
    This class provides methods to safely read from and write to JSON files
    with file locking to prevent data corruption from concurrent access.
    """
    def __init__(self, filename):
        """
        Initialize a JSONFileHandler instance.
        
        Args:
            filename (str): Path to the JSON file to be handled.
        """
        self.file_path = Path(filename)
        self.lock = FileLock(f"{filename}.lock")

    def load(self):
        """
        Load data from the JSON file with file locking.
        
        Returns:
            list or dict: The data loaded from the JSON file, or an empty list if the file doesn't exist.
            
        Note:
            This method acquires a file lock before reading to prevent concurrent access issues.
        """
        with self.lock:
            if not self.file_path.exists():
                return []
            with self.file_path.open("r", encoding="utf-8") as file:
                return json.load(file)

    def save(self, data):
        """
        Save data to the JSON file with file locking.
        
        Args:
            data (list or dict): The data to be saved to the JSON file.
            
        Note:
            This method acquires a file lock before writing to prevent concurrent access issues.
            The data is saved with an indent of 4 spaces for readability.
        """
        with self.lock:
            with self.file_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
