import json
import pyEA.icon as icon
from typing import *
import pyEA
import pyEA.text as text
import os
from pyEA import mapsprite
from pyEA import portrait
from pyEA import animations


def repoint_class_tables():
    if "PortraitTable" not in pyEA.TABLES:
        pyEA.table("PortraitTable", 28, 512)
        pyEA.repoint("PortraitTable", 224, (0x5524,))
    pyEA.table("ClassTable", 84, 256, 1)
    pyEA.repoint("ClassTable", 128, (0x19458, 0x18DAC, 0x17DBC, 0x17AB8))
    pyEA.table("AnimTable", 32, 512, 201)
    pyEA.repoint("AnimTable", 201, (0x59BD8, 0x5A600, 0x5A694, 0x5A82C, 0x6F6A8, 0x70940, 0x70A60))
    pyEA.table("StandingMapSprites", 8, 256, 1)
    pyEA.repoint("StandingMapSprites", 128, (0x26730, 0x267B0, 0x26838, 0x26C88, 0x272D0, 0x27BB0, 0x27C9C,
                                             0x27D48, 0x27E0C, 0x27E9C, 0x27F74, 0x28064,))
    pyEA.table("MovingMapSprites", 8, 256, 1)
    pyEA.repoint("MovingMapSprites", 128, (0x79584, 0x79598, 0xBAC2C, 0xBAC40))
    pyEA.table("PromoBranches", 2, 256, 1)
    pyEA.repoint("PromoBranches", 128, (0xCC7D0, 0xCC824, 0xCC860, 0xCC8A4, 0xCC8EC, 0xCCE8C, 0xCDB74))
    with pyEA.offset(0xCC7C8):
        pyEA.write_ptr1("PromoBranches")
    pyEA.table("MagClassTable", 2, 256, 1)
    pyEA.table("ClassSkillTable", 1, 256, 1)
    pyEA.table("ClassLevelUpSkillTable", 4, 256, 0)
    pyEA.table("ClassLevelCapTable", 1, 256)
    pyEA.table("WalkingSoundTable", 1, 256)


def parse_stats(stats, stat_names):
    for i in stat_names:
        pyEA.write_byte(stats.get(i, 0))
    return stats.get("mag", 0)


def parse_caps(stats, stat_names):
    for i in stat_names:
        pyEA.write_byte(stats.get(i, 60 if i == "hp" else 20))
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
    with open(f"{path}/{filename}.class.json", "r") as file:
        buffer = file.read()
        obj = json.loads(buffer)

    with pyEA.row("ClassTable"):
        offset = pyEA.get_offset()
        name = obj["name"]
        text.write_flex(name, menu=True, width=46, height=1)
        pyEA.globals.set(name.replace(" ", ""), pyEA.current_row("ClassTable"))

        desc = obj.get("description", 0)
        if isinstance(desc, int):
            pyEA.write_short(desc)
        else:
            text.write_flex(desc, menu=False, width=160, height=1)

        class_id = pyEA.current_row("ClassTable") - 1
        pyEA.write_byte(class_id)  # id
        pyEA.write_byte(obj.get("promo", class_id))

        with pyEA.row("PromoBranches"):
            pyEA.write_byte(obj.get("promo", 0))
            pyEA.write_byte(obj.get("promo2", 0))

        pyEA.write_byte(class_id - 1)  # standing_map_anim
        mapsprite.load_standing_sprite(path, filename, free_space, class_id - 1, obj.get("pattern", 2))
        mapsprite.load_moving_sprite(path, filename, free_space, class_id - 1, obj.get("AP", 0x1C692C))
        pyEA.write_byte(1 if "armored" in obj else 0)
        pyEA.write_short(class_id + 256)  # class card
        portrait.load_class_card(path, filename, free_space, class_id + 256)
        pyEA.write_byte(obj.get("sort_order", 5))
        mag = parse_stats(obj.get("bases"), ("hp", "str", "skl", "spe", "def", "res", "con", "move"))
        mag_caps = parse_caps(obj.get("caps"), ("hp", "str", "skl", "spe", "def", "res", "con"))
        pyEA.write_byte(obj.get("relative_power", 3))
        mag_growth = parse_stats(obj.get("growths"), ("hp", "str", "skl", "spe", "def", "res", "luck"))
        mag_promo = parse_stats(obj.get("promo_bonus"), ("hp", "str", "skl", "spe", "def", "res"))
        pyEA.write_word(pyEA.bitfield(obj.get("abilities", ())))
        parse_ranks(obj.get("ranks"))
        print(pyEA.get_offset() - offset)

        with pyEA.alloc(free_space):
            animations.load_animations(path, filename)
        pyEA.write_ptr(obj.get("move_costs", 0x80B849))
        pyEA.write_ptr(obj.get("rain_move_costs", obj.get("move_costs", 0x80BC9A)))
        pyEA.write_ptr(obj.get("snow_move_costs", obj.get("move_costs", 0x80C0AA)))
        pyEA.write_ptr(obj.get("terrain_avoid", 0x80C479))
        pyEA.write_ptr(obj.get("terrain_defense", 0x80C4BA))
        pyEA.write_ptr(obj.get("terrain_resistance", 0x80C4FB))
        pyEA.write_word(pyEA.bitfield(obj.get("class_type", ()), "Unit"))

        with pyEA.row("MagClassTable", class_id):
            pyEA.write_byte(mag, mag_growth, mag_caps, mag_promo)
        skills = obj.get("skills", None)
        if skills is not None:
            with pyEA.row("ClassSkillTable", class_id):
                pyEA.write_byte(skills.get("personal", 0))
            level_up_skills = skills.get("level_up", None)
            if level_up_skills is not None:
                with pyEA.row("ClassLevelUpSkillTable", class_id):
                    with pyEA.alloc(free_space):
                        for i in level_up_skills:
                            pyEA.write_byte(i.get("level", 1))
                            pyEA.write_byte(i["name"])
                        pyEA.write_byte(0, 0)
            else:
                with pyEA.row("ClassLevelUpSkillTable", class_id):
                    pyEA.write_word(0)
        else:
            with pyEA.row("ClassSkillTable", class_id):
                pyEA.write_byte(0)
            with pyEA.row("ClassLevelUpSkillTable", class_id):
                pyEA.write_word(0)
        return b""

