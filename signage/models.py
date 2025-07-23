from datetime import datetime
import os
from typing import Optional, Union

from datetime import datetime

class Slide:
    def __init__(self, source: str, duration: int, start: Optional[datetime] = None, 
                 end: Optional[datetime] = None, hide: bool = False) -> None:
        self.source: str = source
        self.duration: int = duration
        self.start: Optional[datetime] = start if start else None
        self.end: Optional[datetime] = end if end else None
        self.hide: bool = hide

    def is_active(self) -> bool:
        if self.hide:
            return False

        now: datetime = datetime.now()

        if not self.start and not self.end:
            return True

        if not self.start and self.end:
            return now <= self.end

        if self.start and not self.end:
            return now >= self.start

        if self.start and self.end:
            return self.start <= now <= self.end

        return False

