from pyEA import *
from pyEA.FE8.offsets import *
import pyEA.text
from pyEA.convo import Convo
import pyEA.items, pyEA.classes, pyEA.units


load_source("FE8_clean.gba")

# resize the numpy buffer, without this FreeSpaceStream cannot be used
expand_data()

# Free space that starts from 0x1000000, almost unlimited size but will increase rom size
FreeSpaceStream = NpStream(pyEA.BUFFER, FreeSpace, FreeSpaceLength)

# Free space that starts in BL range, small, should be used by engine hacks
FreeSpaceBLStream = NpStream(pyEA.BUFFER, FreeSpaceBLRange, FreeSpace1Length)

# Medium sized free space, does not affect rom size
FreeSpace1Stream = NpStream(pyEA.BUFFER, FreeSpace1, FreeSpace1Length)

# Relatively small free space, does not affect rom size
FreeSpace2Stream = NpStream(pyEA.BUFFER, FreeSpace2, FreeSpace2Length)

# Medium sized free space, does not affect rom size
EndSpaceStream = NpStream(pyEA.BUFFER, EndSpace, EndSpaceLength)

# should be called after tempering with fonts
pyEA.text.populate()

offset(FreeSpace2Stream)

text.repoint_text_table()
pyEA.items.repoint_item_tables()
pyEA.units.repoint_unit_tables()
pyEA.classes.repoint_class_tables()


item_name = 56
item_desc = 160
chara_name = 46


text.write_flex("Silver Rapier", menu=True, width=56, row=0x40C)

Eirika = 1
Ephraim = 2

from pyEA.FE8.text_codes import *

print(pyEA.text.measure_string("You will be the first to die!"))
print(pyEA.text.flex("You will be the first to die!", height=3, width=60).replace(NL, "[N]\n"))

c = Convo()

c.load(Eirika, ML)
c.load(Ephraim, MR)

c.switch(Eirika)
c.build_dialogue(f"Hello, I'm Eirika")

c.switch(Ephraim)
c.build_dialogue(f"I don't pick fights I can't win.")

c.move(Ephraim, RL)
c.build_dialogue(f"I moved to the left!")

c.write()

# should be called after ALL text have been added
text.dump_text()
output("HackRom.gba")


expose("sym.event", True)
