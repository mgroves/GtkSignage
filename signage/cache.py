"""
Cache Module

This module provides functionality for caching URL content locally.
It handles downloading and caching HTML and supporting files (JS, CSS, images),
as well as managing cache expiration and cleanup.
"""
import os
import time
import logging
import hashlib
import shutil
import re
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Get logger for this module
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Default cache settings
DEFAULT_CACHE_DIR = "cache"
DEFAULT_CACHE_EXPIRY_HOURS = 48

# Get cache settings from environment variables
CACHE_DIR = os.getenv("CACHE_DIR", DEFAULT_CACHE_DIR)
CACHE_EXPIRY_HOURS = int(os.getenv("CACHE_EXPIRY_HOURS", DEFAULT_CACHE_EXPIRY_HOURS))


class URLCache:
    """
    A class for caching URL content locally.
    
    This class provides methods for downloading and caching HTML and supporting files,
    as well as managing cache expiration and cleanup.
    """
    
    @classmethod
    def get_cache_path(cls, url):
        """
        Get the cache path for a URL.
        
        Args:
            url (str): The URL to get the cache path for.
            
        Returns:
            Path: The path to the cached file.
        """
        # Create a hash of the URL to use as the filename
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        # Create the cache directory if it doesn't exist
        cache_dir = Path(CACHE_DIR)
        if not cache_dir.exists():
            logger.info(f"Creating cache directory: {cache_dir}")
            cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Return the path to the cached file
        return cache_dir / f"{url_hash}.html"
    
    @classmethod
    def get_cache_dir_for_url(cls, url):
        """
        Get the cache directory for a URL's supporting files.
        
        Args:
            url (str): The URL to get the cache directory for.
            
        Returns:
            Path: The path to the cache directory for the URL.
        """
        # Create a hash of the URL to use as the directory name
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        # Create the cache directory if it doesn't exist
        cache_dir = Path(CACHE_DIR) / url_hash
        if not cache_dir.exists():
            logger.info(f"Creating cache directory for URL: {cache_dir}")
            cache_dir.mkdir(parents=True, exist_ok=True)
        
        return cache_dir
    
    @classmethod
    def is_cached(cls, url):
        """
        Check if a URL is cached.
        
        Args:
            url (str): The URL to check.
            
        Returns:
            bool: True if the URL is cached, False otherwise.
        """
        cache_path = cls.get_cache_path(url)
        return cache_path.exists()
    
    @classmethod
    def is_cache_expired(cls, url):
        """
        Check if the cache for a URL is expired.
        
        Args:
            url (str): The URL to check.
            
        Returns:
            bool: True if the cache is expired, False otherwise.
        """
        cache_path = cls.get_cache_path(url)
        if not cache_path.exists():
            return True
        
        # Get the modification time of the cached file
        mtime = cache_path.stat().st_mtime
        mtime_dt = datetime.fromtimestamp(mtime)
        
        # Check if the cache is expired
        expiry_time = datetime.now() - timedelta(hours=CACHE_EXPIRY_HOURS)
        return mtime_dt < expiry_time
    
    @classmethod
    def cache_url(cls, url):
        """
        Cache a URL and its supporting files.
        
        Args:
            url (str): The URL to cache.
            
        Returns:
            bool: True if the URL was cached successfully, False otherwise.
        """
        logger.info(f"Caching URL: {url}")
        
        try:
            # Download the HTML content
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text
            
            # Parse the HTML to find supporting files
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Get the base URL for resolving relative URLs
            base_url = url
            base_tag = soup.find('base')
            if base_tag and base_tag.get('href'):
                base_url = urllib.parse.urljoin(url, base_tag['href'])
            
            # Cache supporting files
            cache_dir = cls.get_cache_dir_for_url(url)
            url_hash = hashlib.md5(url.encode()).hexdigest()
            
            # Cache CSS files and update references
            for css_tag in soup.find_all('link', rel='stylesheet'):
                if css_tag.get('href'):
                    success, cache_filename, original_url = cls._cache_supporting_file(css_tag['href'], base_url, cache_dir, 'css')
                    if success and cache_filename:
                        # Update the href to point to the cached file with absolute file:// URL
                        cached_file_path = cache_dir / cache_filename
                        css_tag['href'] = f"file://{cached_file_path.absolute()}"
            
            # Cache JavaScript files and update references
            for js_tag in soup.find_all('script', src=True):
                success, cache_filename, original_url = cls._cache_supporting_file(js_tag['src'], base_url, cache_dir, 'js')
                if success and cache_filename:
                    # Update the src to point to the cached file with absolute file:// URL
                    cached_file_path = cache_dir / cache_filename
                    js_tag['src'] = f"file://{cached_file_path.absolute()}"
            
            # Cache images and update references
            for img_tag in soup.find_all('img', src=True):
                success, cache_filename, original_url = cls._cache_supporting_file(img_tag['src'], base_url, cache_dir, 'img')
                if success and cache_filename:
                    # Update the src to point to the cached file with absolute file:// URL
                    cached_file_path = cache_dir / cache_filename
                    img_tag['src'] = f"file://{cached_file_path.absolute()}"
            
            # Cache the modified HTML content
            cache_path = cls.get_cache_path(url)
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            
            logger.info(f"Successfully cached URL: {url}")
            return True
        
        except Exception as e:
            logger.error(f"Error caching URL {url}: {e}")
            return False
    
    @classmethod
    def _cache_supporting_file(cls, relative_url, base_url, cache_dir, file_type):
        """
        Cache a supporting file (CSS, JS, image, etc.).
        
        Args:
            relative_url (str): The relative URL of the file.
            base_url (str): The base URL for resolving relative URLs.
            cache_dir (Path): The directory to cache the file in.
            file_type (str): The type of file (css, js, img, etc.).
            
        Returns:
            tuple: (bool, str, str) - Success status, cached filename, and original URL.
                   If caching failed, returns (False, None, None).
        """
        try:
            # Resolve the absolute URL
            absolute_url = urllib.parse.urljoin(base_url, relative_url)
            
            # Create a filename for the cached file
            url_hash = hashlib.md5(absolute_url.encode()).hexdigest()
            
            # Extract the file extension from the URL
            parsed_url = urllib.parse.urlparse(absolute_url)
            path = parsed_url.path
            extension = os.path.splitext(path)[1]
            if not extension:
                extension = f".{file_type}"
            
            # Create the cache filename
            cache_filename = f"{url_hash}{extension}"
            cache_path = cache_dir / cache_filename
            
            # Download and cache the file
            response = requests.get(absolute_url, timeout=10)
            response.raise_for_status()
            
            with open(cache_path, 'wb') as f:
                f.write(response.content)
            
            logger.debug(f"Cached supporting file: {absolute_url} -> {cache_path}")
            return True, cache_filename, relative_url
        
        except Exception as e:
            logger.error(f"Error caching supporting file {relative_url}: {e}")
            return False, None, None
    
    @classmethod
    def get_cached_url(cls, url):
        """
        Get the cached URL.
        
        Args:
            url (str): The original URL.
            
        Returns:
            str: The file:// URL to the cached file, or the original URL if not cached.
        """
        if not cls.is_cached(url):
            return url
        
        cache_path = cls.get_cache_path(url)
        return f"file://{cache_path.absolute()}"
    
    @classmethod
    def cleanup_expired_cache(cls):
        """
        Clean up expired cache files.
        
        This method removes all cached files that are older than the expiry time.
        """
        logger.info("Cleaning up expired cache files")
        
        try:
            cache_dir = Path(CACHE_DIR)
            if not cache_dir.exists():
                logger.debug("Cache directory does not exist, nothing to clean up")
                return
            
            # Get the expiry time
            expiry_time = time.time() - (CACHE_EXPIRY_HOURS * 3600)
            
            # Check all files and directories in the cache directory
            for item in cache_dir.iterdir():
                if item.is_file():
                    # Check if the file is expired
                    mtime = item.stat().st_mtime
                    if mtime < expiry_time:
                        logger.debug(f"Removing expired cache file: {item}")
                        item.unlink()
                elif item.is_dir():
                    # Check if the directory is expired (based on the directory's mtime)
                    mtime = item.stat().st_mtime
                    if mtime < expiry_time:
                        logger.debug(f"Removing expired cache directory: {item}")
                        shutil.rmtree(item)
            
            logger.info("Finished cleaning up expired cache files")
        
        except Exception as e:
            logger.error(f"Error cleaning up expired cache files: {e}")