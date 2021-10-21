import json
import pyEA.icon as icon
from typing import *
import pyEA
import pyEA.textengine as text

WEAPONS = [0, 1, 2, 3, 4, 5, 6, 7, 0xb, 0x11]
TOMES = [5, 6, 7]
TOMES_ALWAYS_ATTACK_RES = True


def repoint_item_tables():
    pyEA.table("weapon_locks", pyEA.PTR, 256, 1, b"\x00\x00\x00\x00")

    pyEA.table("item_icon_table", 128, 256)
    pyEA.repoint("item_icon_table", 224, (0x36B4, 0x3788))

    pyEA.table("item_table", 36, 256, 0xBC)
    pyEA.repoint("item_table", 224, (0x16410, 0x16440, 0x16470, 0x164A0, 0x164D0, 0x16530, 0x16500, 0x16570, 0x166D0,
                                     0x1671C, 0x1678C, 0x167E0, 0x1683C, 0x168C4, 0x1683C, 0x1698C, 0x16A10, 0x16AD0,
                                     0x16B18, 0x16BB4, 0x16C14, 0x16C7C, 0x16D04, 0x16DD4, 0x16F0C, 0x16FA4, 0x17028,
                                     0x1707C, 0x170C8, 0x170F8, 0x1727C, 0x172D8, 0x1735C, 0x173AC, 0x17420, 0x174A4,
                                     0x174E4, 0x17514, 0x1752C, 0x17544, 0x17560, 0x17580, 0x175A4, 0x175A4, 0x175D0,
                                     0x175F0, 0x17608, 0x17620, 0x17638, 0x1765C, 0x17680, 0x1769C, 0x176B4, 0x176CC,
                                     0x176E4, 0x176FC, 0x17718, 0x17738, 0x17750, 0x17768,
                                     0x17794, 0x177AC, 0x177C0, 0x17718, 0x1C1FB8, 0x1C20E0))


def parse_weapon_lock_array(weapon_lock_array: Union[None, List[Union[str, int]], Dict[str, Any]]):
    if weapon_lock_array is None:
        return
    if isinstance(weapon_lock_array, list):
        pyEA.write_byte(1)
    else:
        pyEA.write_byte(weapon_lock_array["type"])
        weapon_lock_array = weapon_lock_array["array"]
    for i in weapon_lock_array:
        pyEA.write_byte(i)
    pyEA.write_byte(0)


def parse_stat_boosts(stat_boosts):
    if stat_boosts is None:
        return
    pyEA.write_byte(stat_boosts.get("hp", 0))
    pyEA.write_byte(stat_boosts.get("str", 0))
    pyEA.write_byte(stat_boosts.get("skl", 0))
    pyEA.write_byte(stat_boosts.get("spe", stat_boosts.get("spd", 0)))
    pyEA.write_byte(stat_boosts.get("def", 0))
    pyEA.write_byte(stat_boosts.get("res", 0))
    pyEA.write_byte(stat_boosts.get("lck", 0))
    pyEA.write_byte(stat_boosts.get("move", 0))
    pyEA.write_byte(stat_boosts.get("con", 0))
    pyEA.write_byte(stat_boosts.get("mag", 0))
    pyEA.write_byte(0, 0)


def parse_effectiveness(effectiveness):
    if effectiveness is None:
        return 0
    if effectiveness is dict:
        effectiveness = [effectiveness]
    for i in effectiveness:
        pyEA.write_byte(0, round(i["x"] * 2))
        pyEA.write_short(pyEA.bitfield(i["types"]))
    pyEA.write_word(0)


def parse_range(range_obj):
    if range_obj == "all":
        return 0xFF
    elif range_obj == "staff":
        return 0x10
    elif isinstance(range_obj, int):
        if range_obj > 0xF:
            return range_obj
        return (range_obj << 4) + range_obj
    else:
        return range_obj[1] + (range_obj[0] << 4)


def parse_rank(rank):
    if isinstance(rank, int):
        return rank
    if isinstance(rank, str):
        if len(rank) == 1:
            rank = rank.upper() + "Rank"
        return pyEA.fetch(rank)
    return 0


def parse_item(path, filename):
    free_space = pyEA.STREAM
    with open(f"{path}/{filename}.item", "r") as file:
        buffer = file.read()
        obj = json.loads(buffer)

    with pyEA.row("item_table"):
        name = obj["name"]
        text.write_flex(name, menu=True, width=56, height=1)
        pyEA.globals.set(name.replace(" ", ""), pyEA.current_row("item_table"))

        desc = obj.get("description", 403)
        if isinstance(desc, int):
            pyEA.write_short(desc)
        else:
            text.write_flex(desc, menu=False, width=160, height=1)

        use_text = obj.get("use_text", 403)
        if isinstance(use_text, int):
            pyEA.write_short(use_text)
        else:
            text.write_flex(use_text, menu=False, width=160, height=1)

        pyEA.write_byte(pyEA.current_row("item_table") - 1)  # id
        weapon_type = pyEA.fetch(obj.get("type", 9))
        pyEA.write_byte(weapon_type)
        ability = pyEA.bitfield(obj.get("ability", ()))
        if weapon_type in WEAPONS:
            ability |= 1
        if TOMES_ALWAYS_ATTACK_RES and weapon_type in TOMES:
            ability |= 2
        pyEA.write_word(ability)
        pyEA.advance(-1)
        weapon_lock = obj.get("weapon_locks", None)
        if weapon_lock is not None:
            with pyEA.write_row(pyEA.BYTE, "weapon_locks"):
                with pyEA.alloc(free_space):
                    parse_weapon_lock_array(obj.get("weapon_locks", None))
        else:
            pyEA.write_byte(0)

        boosts = obj.get("stats", None)
        if boosts is not None:
            with pyEA.alloc(free_space):
                parse_stat_boosts(boosts)
        else:
            pyEA.write_word(0)
        effs = obj.get("effective", None)
        if effs is not None:
            with pyEA.alloc(free_space):
                parse_stat_boosts(effs)
        else:
            pyEA.write_word(0)
        uses = obj.get("uses", 1)
        pyEA.write_byte(uses)
        pyEA.write_byte(obj.get("might", 0))
        pyEA.write_byte(obj.get("hit", 0))
        pyEA.write_byte(obj.get("weight", 0))
        pyEA.write_byte(obj.get("crit", 0))
        pyEA.write_byte(parse_range(obj.get("range", 0)))
        pyEA.write_short(obj.get("price", obj.get("price_total", 0) / uses))
        pyEA.write_byte(parse_rank(obj.get("rank", 0)))
        pyEA.write_byte(pyEA.current_row("item_icon_table"))
        with pyEA.row("item_icon_table"):
            pyEA.write(icon.load_item_icon(path, filename))
        pyEA.write_byte(obj.get("use_effect", 0))
        pyEA.write_byte(obj.get("damage_effect", 0))
        pyEA.write_byte(obj.get("wexp", 1))
        pyEA.write_byte(obj.get("debuffs", 1))
        pyEA.write_byte(obj.get("23", 1))
        pyEA.write_byte(obj.get("skill", 1))
        return b""

