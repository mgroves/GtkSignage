from datetime import datetime
import os

from datetime import datetime

class Slide:
    def __init__(self, source, duration, start=None, end=None, hide=False):
        self.source = source
        self.duration = duration
        self.start = start if start else None
        self.end = end if end else None
        self.hide = hide

    def is_active(self):
        if self.hide:
            return False

        now = datetime.now()

        if not self.start and not self.end:
            return True

        if not self.start and self.end:
            return now <= self.end

        if self.start and not self.end:
            return now >= self.start

        if self.start and self.end:
            return self.start <= now <= self.end

        return False

