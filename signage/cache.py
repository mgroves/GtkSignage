"""
Cache Module

Provides functionality for caching URL content locally.
Handles downloading HTML and supporting files (JS, CSS, images),
cache expiration, and cleanup.
"""

from __future__ import annotations

import time
import logging
import hashlib
import shutil
import os
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from signage.config import get_int, get_path

logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

CACHE_DIR: Path = get_path("cache", "dir", default="cache")
CACHE_EXPIRY_HOURS: int = get_int("cache", "expiry_hours", default=48)


class URLCache:
    """
    Utility class for caching URL content locally.
    """

    # ------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------

    @classmethod
    def _ensure_cache_dir(cls) -> None:
        if not CACHE_DIR.exists():
            logger.info("Creating cache directory: %s", CACHE_DIR)
            CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_cache_path(cls, url: str) -> Path:
        """
        Return path to cached HTML file for a URL.
        """
        cls._ensure_cache_dir()
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return CACHE_DIR / f"{url_hash}.html"

    @classmethod
    def get_cache_dir_for_url(cls, url: str) -> Path:
        """
        Return directory for cached supporting files for a URL.
        """
        cls._ensure_cache_dir()
        url_hash = hashlib.md5(url.encode()).hexdigest()
        path = CACHE_DIR / url_hash
        path.mkdir(parents=True, exist_ok=True)
        return path

    # ------------------------------------------------------------
    # Cache status
    # ------------------------------------------------------------

    @classmethod
    def is_cached(cls, url: str) -> bool:
        return cls.get_cache_path(url).exists()

    @classmethod
    def is_cache_expired(cls, url: str) -> bool:
        cache_path = cls.get_cache_path(url)
        if not cache_path.exists():
            return True

        mtime = cache_path.stat().st_mtime
        expiry_time = datetime.now() - timedelta(hours=CACHE_EXPIRY_HOURS)
        return datetime.fromtimestamp(mtime) < expiry_time

    # ------------------------------------------------------------
    # Caching
    # ------------------------------------------------------------

    @classmethod
    def cache_url(cls, url: str) -> bool:
        """
        Cache a URL and its supporting files.
        """
        logger.info("Caching URL: %s", url)

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text

            soup = BeautifulSoup(html_content, "html.parser")

            base_url = url
            base_tag = soup.find("base")
            if base_tag and base_tag.get("href"):
                base_url = urllib.parse.urljoin(url, base_tag["href"])

            cache_dir = cls.get_cache_dir_for_url(url)

            # Stylesheets
            for tag in soup.find_all("link", rel="stylesheet"):
                if tag.get("href"):
                    success, filename = cls._cache_supporting_file(
                        tag["href"], base_url, cache_dir, "css"
                    )
                    if success:
                        tag["href"] = f"file://{(cache_dir / filename).absolute()}"

            # Scripts
            for tag in soup.find_all("script", src=True):
                success, filename = cls._cache_supporting_file(
                    tag["src"], base_url, cache_dir, "js"
                )
                if success:
                    tag["src"] = f"file://{(cache_dir / filename).absolute()}"

            # Images
            for tag in soup.find_all("img", src=True):
                success, filename = cls._cache_supporting_file(
                    tag["src"], base_url, cache_dir, "img"
                )
                if success:
                    tag["src"] = f"file://{(cache_dir / filename).absolute()}"

            cache_path = cls.get_cache_path(url)
            cache_path.write_text(str(soup), encoding="utf-8")

            logger.info("Successfully cached URL: %s", url)
            return True

        except Exception as e:
            logger.error("Error caching URL %s: %s", url, e)
            return False

    @classmethod
    def _cache_supporting_file(
        cls,
        relative_url: str,
        base_url: str,
        cache_dir: Path,
        file_type: str,
    ) -> tuple[bool, str | None]:
        try:
            absolute_url = urllib.parse.urljoin(base_url, relative_url)
            url_hash = hashlib.md5(absolute_url.encode()).hexdigest()

            parsed = urllib.parse.urlparse(absolute_url)
            ext = os.path.splitext(parsed.path)[1] or f".{file_type}"

            filename = f"{url_hash}{ext}"
            path = cache_dir / filename

            response = requests.get(absolute_url, timeout=10)
            response.raise_for_status()

            path.write_bytes(response.content)

            logger.debug("Cached %s -> %s", absolute_url, path)
            return True, filename

        except Exception as e:
            logger.error("Error caching %s: %s", relative_url, e)
            return False, None

    # ------------------------------------------------------------
    # Access
    # ------------------------------------------------------------

    @classmethod
    def get_cached_url(cls, url: str) -> str:
        if not cls.is_cached(url):
            return url
        return f"file://{cls.get_cache_path(url).absolute()}"

    # ------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------

    @classmethod
    def cleanup_expired_cache(cls) -> None:
        logger.info("Cleaning up expired cache files")

        if not CACHE_DIR.exists():
            return

        expiry_time = time.time() - (CACHE_EXPIRY_HOURS * 3600)

        try:
            for item in CACHE_DIR.iterdir():
                if item.stat().st_mtime < expiry_time:
                    if item.is_file():
                        logger.debug("Removing expired cache file: %s", item)
                        item.unlink()
                    elif item.is_dir():
                        logger.debug("Removing expired cache dir: %s", item)
                        shutil.rmtree(item)

            logger.info("Cache cleanup complete")

        except Exception as e:
            logger.error("Cache cleanup failed: %s", e)