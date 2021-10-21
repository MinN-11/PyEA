from pyEA import *
from FE8.definitions import *
import pyEA.textengine
from pyEA.convo import Convo

load_source("FE8_clean.gba")

# resize the numpy buffer, without this, FreeSpaceStream cannot be used
expand_data()

# A free space that starts from 0x1000000, almost unlimited size but will increase rom size
FreeSpaceStream = NpStream(pyEA.BUFFER, FreeSpace, FreeSpaceLength)

# A free space that starts in BL range, small, should be used by engine hacks
FreeSpaceBLStream = NpStream(pyEA.BUFFER, FreeSpaceBLRange, FreeSpace1Length)

# A medium sized free space, does not affect rom size
FreeSpace1Stream = NpStream(pyEA.BUFFER, FreeSpace1, FreeSpace1Length)

# A relatively small free space, does not affect rom size
FreeSpace2Stream = NpStream(pyEA.BUFFER, FreeSpace2, FreeSpace2Length)

# A medium sized free space, does not affect rom size
EndSpaceStream = NpStream(pyEA.BUFFER, EndSpace, EndSpaceLength)

offset(FreeSpace2Stream)

# should be called after tempering with fonts
pyEA.textengine.populate()

print(pyEA.textengine.measure_string("You will be the first to die!"))
print(pyEA.textengine.write_flex("You will be the first to die!", height=3, width=60))

item_name = 56
item_desc = 160
chara_name = 46

with offset(0xA26C):
    with offset(peek(POIN)):
        table("text", PTR, 0x1000, 0xD48)

table("text", PTR, 0x1000, 0xD48, 0xE8414.to_bytes(4, "little"))
repoint("text", 0x15D48C, 0xD48, (0xA26C, 0xA2A0))

with row("text", 0x40C):
    with alloc_text(FreeSpace2Stream):
        print(pyEA.textengine.write_flex("Silver Rapier", menu=True, width=56))
        textengine.write_text(pyEA.textengine.write_flex("Silver Rapier", menu=True, width=56))


Eirika = 1
Ephraim = 2

from FE8.text_codes import *

c = Convo()

c.load(Eirika, ML)
c.load(Ephraim, MR)

c.switch(Eirika)
c.build_dialogue(f"{MID_BLINK}Hello, I'm Eirika{MID_BLINK}")

c.switch(Ephraim)
c.build_dialogue(f"{RED}I don't pick fights I can't win.{RED}")

c.move(Ephraim, RL)
c.build_dialogue(f"I moved to the left!")

c.write()


# should be called after ALL text have been "added"
textengine.dump_text()
output("HackRom.gba")


