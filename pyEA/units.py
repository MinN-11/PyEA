import json
import pyEA.portrait as portrait
import pyEA
import pyEA.textengine as text
import os


def repoint_unit_tables():
    if "PortraitTable" not in pyEA.TABLES:
        pyEA.table("PortraitTable", 28, 512)
        pyEA.repoint("PortraitTable", 224, (0x5524,))
    pyEA.table_from(0x17D64, "UnitTable", 52, 256, 1)
    pyEA.table("MagCharTable", 2, 256, 1)
    pyEA.table("PersonalSkillTable", 1, 256, 1)
    pyEA.table("CharLevelUpSkillTable", 4, 256, 1)


def parse_stats(stats, stat_names):
    for i in stat_names:
        pyEA.write_byte(stats.get(i, 0))
    return stats.get("mag", 0)


RANKS = ("sword", "lance", "axe", "bow", "staff", "anima", "light", "dark")


def parse_ranks(ranks):
    for i in RANKS:
        rank = ranks.get(i, 0)
        if isinstance(rank, str):
            rank = rank.upper() + "Rank"
        pyEA.write_byte(rank)


def parse_unit(path, filename):
    free_space = pyEA.STREAM
    with open(f"{path}/{filename}.unit.json", "r") as file:
        buffer = file.read()
        obj = json.loads(buffer)

    with pyEA.row("UnitTable"):
        name = obj["name"]
        text.write_flex(name, menu=True, width=46, height=1)
        unit_id = pyEA.current_row("UnitTable") - 1
        pyEA.globals.set(name.replace(" ", ""), unit_id)

        desc = obj.get("description", 0)
        if isinstance(desc, int):
            pyEA.write_short(desc)
        else:
            text.write_flex(desc, menu=False, width=160, height=1)

        pyEA.write_byte(unit_id)  # id
        pyEA.write_byte(obj.get("class", 5))  # using cavs, probably the most stable slot

        if os.path.isfile(f"{path}/{filename}.png"):
            portrait.load_portrait(path, filename, free_space, unit_id)
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
        with pyEA.row("MagCharTable", unit_id):
            pyEA.write_byte(mag, mag_growth)
        skills = obj.get("skills", None)
        if skills is not None:
            with pyEA.row("PersonalSkillTable", unit_id):
                pyEA.write_byte(skills.get("personal", 0))
            level_up_skills = skills.get("level_up", None)
            if level_up_skills is not None:
                with pyEA.row("CharLevelUpSkillTable", unit_id):
                    with pyEA.alloc(free_space):
                        for i in level_up_skills:
                            pyEA.write_byte(i.get("level", 1))
                            pyEA.write_byte(i["name"])
                        pyEA.write_byte(0, 0)
            else:
                with pyEA.row("CharLevelUpSkillTable", unit_id):
                    pyEA.write_word(0)
        else:
            with pyEA.row("PersonalSkillTable", unit_id):
                pyEA.write_byte(0)
            with pyEA.row("CharLevelUpSkillTable", unit_id):
                pyEA.write_word(0)
        return b""

