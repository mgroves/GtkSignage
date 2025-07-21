from datetime import datetime
import os

class Slide:
    def __init__(self, source, duration, start=None, end=None):
        self.source = source
        self.duration = duration
        self.start = start or datetime.min
        self.end = end or datetime.max

    def is_active(self):
        now = datetime.now()
        return self.start <= now <= self.end