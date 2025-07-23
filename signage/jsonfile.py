"""
JSON File Handler Module

This module provides functionality for safely reading from and writing to JSON files
with file locking to prevent concurrent access issues.
"""
import json
import logging
from pathlib import Path

from filelock import FileLock

# Get logger for this module
logger = logging.getLogger(__name__)

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
        logger.debug(f"Acquiring lock for reading: {self.file_path}")
        with self.lock:
            logger.debug(f"Lock acquired for reading: {self.file_path}")
            if not self.file_path.exists():
                logger.info(f"File does not exist, returning empty list: {self.file_path}")
                return []
            try:
                with self.file_path.open("r", encoding="utf-8") as file:
                    logger.debug(f"Reading file: {self.file_path}")
                    data = json.load(file)
                    logger.debug(f"Successfully loaded data from: {self.file_path}")
                    return data
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in {self.file_path}: {e}")
                return []
            except Exception as e:
                logger.error(f"Error reading {self.file_path}: {e}")
                return []

    def save(self, data):
        """
        Save data to the JSON file with file locking.
        
        Args:
            data (list or dict): The data to be saved to the JSON file.
            
        Note:
            This method acquires a file lock before writing to prevent concurrent access issues.
            The data is saved with an indent of 4 spaces for readability.
        """
        logger.debug(f"Acquiring lock for writing: {self.file_path}")
        with self.lock:
            logger.debug(f"Lock acquired for writing: {self.file_path}")
            try:
                # Ensure parent directory exists
                parent_dir = self.file_path.parent
                if not parent_dir.exists():
                    logger.info(f"Creating parent directory: {parent_dir}")
                    parent_dir.mkdir(parents=True, exist_ok=True)
                
                logger.debug(f"Writing data to file: {self.file_path}")
                with self.file_path.open("w", encoding="utf-8") as file:
                    json.dump(data, file, indent=4)
                logger.debug(f"Successfully saved data to: {self.file_path}")
            except PermissionError as e:
                logger.error(f"Permission error writing to {self.file_path}: {e}")
                raise
            except OSError as e:
                logger.error(f"OS error writing to {self.file_path}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error writing to {self.file_path}: {e}")
                raise
