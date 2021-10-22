import json
import pyEA.icon as icon
from typing import *
import pyEA
import pyEA.textengine as text
import os


def repoint_class_tables():
    if "PortraitTable" not in pyEA.TABLES:
        pyEA.table("PortraitTable", 28, 512)
        pyEA.repoint("PortraitTable", 224, (0x5524,))
    pyEA.table("ClassTable", 84, 256, 1)
    pyEA.repoint("ClassTable", 128, (0x19458, 0x18DAC, 0x17DBC, 0x17AB8))
    pyEA.table("AnimTable", 32, 512, 201)
    pyEA.repoint("AnimTable", 201, (0x59BD8, 0x5A600, 0x5A694, 0x5A82C, 0x6F6A8, 0x70940, 0x70A60))
    pyEA.table("MagClassTable", 2, 256, 1)
    pyEA.table("ClassSkillTable", 1, 256, 1)
    pyEA.table("ClassLevelUpSkillTable", 4, 256, 0)


def parse_stats(stats, stat_names):
    for i in stat_names:
        pyEA.write_byte(stats.get("hp", 0))
    pyEA.write_byte(0, 0)
    return stats.get("mag", 0)


RANKS = ("sword", "lance", "axe", "bow", "staff", "anima", "light", "dark")


def parse_ranks(ranks):
    for i in RANKS:
        rank = ranks.get(i, 0)
        if isinstance(rank, str):
            rank = rank.upper() + "Rank"
        pyEA.write_byte(rank)


def parse_class(path, filename):
    free_space = pyEA.STREAM
    with open(f"{path}/{filename}.class", "r") as file:
        buffer = file.read()
        obj = json.loads(buffer)

    with pyEA.row("ClassTable"):
        name = obj["name"]
        text.write_flex(name, menu=True, width=46, height=1)
        pyEA.globals.set(name.replace(" ", ""), pyEA.current_row("ClassTable"))

        desc = obj.get("description", 0)
        if isinstance(desc, int):
            pyEA.write_short(desc)
        else:
            text.write_flex(desc, menu=False, width=160, height=1)

        unit_id = pyEA.current_row("ClassTable") - 1
        pyEA.write_byte(unit_id)  # id
        pyEA.write_byte(obj.get("class", 5))  # using cavs, probably the most stable slot

        if os.path.isfile(f"{path}/{filename}.png"):
            # TODO: parse portrait
            pyEA.write_short(unit_id)
            pyEA.write_byte(obj.get("minimug", 0))
        else:
            pyEA.write_short(0)
            pyEA.write_byte(obj.get("minimug", 6))  # red shield
        pyEA.write_byte(obj.get("affinity", 0))
        pyEA.write_byte(obj.get("sort_order", 5))
        pyEA.write_byte(obj.get("lv", 1))
        mag = parse_stats(obj.get("bases"), ("hp", "str", "skl", "spe", "def", "res", "luck", "con"))
        parse_ranks(obj.get("ranks"))
        mag_growth = parse_stats(obj.get("growths"), ("hp", "str", "skl", "spe", "def", "res", "luck"))
        pyEA.write_byte(0, 0, 0, 0, 0)
        pyEA.write_word(pyEA.bitfield(obj.get("abilities", ())))
        pyEA.write_ptr(0)
        pyEA.write_byte(obj.get("convo_group", 0))
        pyEA.write_byte(0, 0, 0)
        with pyEA.row("MagClassTable", unit_id):
            pyEA.write_byte(mag, mag_growth)
        skills = obj.get("skills", None)
        if skills is not None:
            with pyEA.row("ClassSkillTable", unit_id):
                pyEA.write_byte(skills.get("personal", 0))
            level_up_skills = skills.get("level_up", None)
            if level_up_skills is not None:
                with pyEA.row("ClassLevelUpSkillTable", unit_id):
                    with pyEA.alloc(free_space):
                        for i in level_up_skills:
                            pyEA.write_byte(i.get("level", 1))
                            pyEA.write_byte(i["name"])
                        pyEA.write_byte(0, 0)
            else:
                with pyEA.row("ClassLevelUpSkillTable", unit_id):
                    pyEA.write_word(0)
        else:
            with pyEA.row("ClassSkillTable", unit_id):
                pyEA.write_byte(0)
            with pyEA.row("ClassLevelUpSkillTable", unit_id):
                pyEA.write_word(0)
        return b""

