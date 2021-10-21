
import pyEA
import pyEA.textengine as text
from FE8.text_codes import *
from typing import *
import numpy

def auto_a(string: str):
    data = ""
    splits = string.split(NL)
    for i, v in enumerate(splits):
        data += v
        if i % 2 == 0 or i + 1 == len(splits):
            data += A
        if i + 1 != len(splits):
            data += NL
    return data


class Convo:

    def __init__(self):
        self.buffer = ""
        self.refs: Dict[int, str] = {}

    def write(self):
        text.write_text(self.buffer)

    def load(self, character: int, where: str):
        self.refs[character] = where
        self.buffer += where + LOAD + chr(character) + chr(1)

    def switch(self, character: int):
        self.buffer += self.refs[character]

    def move(self, character: int, to: str):
        self.buffer += self.refs[character] + MOVE(to)

    def remove(self, character):
        self.buffer += self.refs[character] + CLEAR

    def build_dialogue(self, string: str):
        self.buffer += auto_a(text.normal(string, width=160, height=99))

    def pause_for_event(self):
        self.buffer += EVENTS

    def choice_box(self, yes=True):
        self.buffer += (YES if yes else NO) + CLEAR
