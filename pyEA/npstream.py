from typing import *
import pyEA
import numpy


class StreamRevert:
    def __init__(self, src):
        self.last: NpStream = src

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pyEA.STREAM = self.last


class NpStream:
    """A BytesIO object designed to modify a numpy array"""
    def __init__(self, buffer: numpy.ndarray, start: int = 0, max: int = 0xFFFFFF):
        self.ptr = start
        self.buffer = buffer
        self.limit = start + max

    def seek(self, offset):
        self.ptr = offset

    def tell(self):
        return self.ptr

    def _limit_check(self):
        if self.ptr > self.limit:
            print("Warning: Reached the end of free space.")
            self.limit = 0xFFFFFFFFFFF

    def write(self, data: Union[bytes, numpy.ndarray]):
        if isinstance(data, bytes):
            data = numpy.frombuffer(data, dtype=numpy.ubyte)
        size = data.shape[0]
        self.buffer[self.ptr: self.ptr + size] = data
        self.ptr += size
        pyEA.DATA_MAX = pyEA.DATA_MAX if pyEA.DATA_MAX >= self.ptr else self.ptr
        self._limit_check()

    def peek(self, size: int):
        return self.buffer[self.ptr: self.ptr + size].tobytes()

    def read(self, size: int):
        a = self.buffer[self.ptr: self.ptr + size].tobytes()
        self.ptr += size
        return a

    def align(self, by):
        self.ptr = (self.ptr + by - 1) // by * by
