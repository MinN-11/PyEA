
import pyEA
from typing import *

class TempOffset:
    """An object, when destroyed in a with block, revert the offset to a previous location."""

    def __init__(self, last: int):
        self.last: int = last
        self.parent: Union[TempOffset, None] = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.parent is not None:
            self.parent.last = pyEA.get_offset()
        self.pop()

    def pop(self):
        """Revert the offset to a previous location."""
        pyEA.STREAM.seek(self.last)

    def alloc(self):
        child = pyEA.offset(self.last)
        child.parent = self
