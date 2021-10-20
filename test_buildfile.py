from pyEA import *
from FE8.definitions import *

load_source("FE8_clean.gba")
expand_data()

FreeSpaceStream = NpStream(pyEA.BUFFER, FreeSpace, FreeSpaceLength)
FreeSpaceBLStream = NpStream(pyEA.BUFFER, FreeSpaceBLRange, FreeSpace1Length)
FreeSpace1Stream = NpStream(pyEA.BUFFER, FreeSpace1, FreeSpace1Length)
FreeSpace2Stream = NpStream(pyEA.BUFFER, FreeSpace2, FreeSpace2Length)
EndSpaceStream = NpStream(pyEA.BUFFER, EndSpace, EndSpaceLength)
offset(FreeSpace1Stream)

table("text", PTR, 0x1000, 0xD48, 0xE8414.to_bytes(4, "little"))
repoint("text", 0x15D48C, 0xD48, (0xA26C, 0xA2A0))
output("HackRom.gba")

