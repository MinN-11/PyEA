import json
import __init__
import icon
from typing import *

WEAPONS = [0, 1, 2, 3, 4, 5, 6, 7, 0xb, 0x11]
TOMES = [5, 6, 7]
TOMES_ALWAYS_ATTACK_RES = True


def parse_weapon_lock_array(weapon_lock_array: Union[None, List[Union[str, int]], Dict[Any]], offset):
    if weapon_lock_array is None:
        return 0
    with offset.alloc():
        if isinstance(weapon_lock_array, list):
            __init__.write_byte(1)
        else:
            __init__.write_byte(weapon_lock_array["type"])
            weapon_lock_array = weapon_lock_array["array"]
        for i in weapon_lock_array:
            __init__.write_byte(i)
        __init__.write_byte(0)


def parse_stat_boosts(stat_boosts, offset):
    if stat_boosts is None:
        return 0
    return 0


def parse_effectiveness(effectiveness, offset):
    if effectiveness is None:
        return 0
    return 0


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
        return range_obj[0] + (range_obj[1] << 4)


def parse_rank(rank):
    if isinstance(rank, int):
        return rank
    if isinstance(rank, str):
        if len(str) == 1:
            rank = rank.upper() + "Rank"
        return __init__.fetch(rank)
    return 0


def parse_item(path):

    obj = json.loads(path + ".item")
    with __init__.row("items") as table_offset:
        with __init__.write_row(__init__.SHORT, "text"):
            __init__.write_string(obj["name"])

        desc = obj.get("description", 403)
        if isinstance(desc, int):
            __init__.write_short(desc)
        else:
            with __init__.write_row(__init__.SHORT, "text"):
                __init__.write_string(desc)

        use_text = obj.get("use_text", 403)
        if isinstance(use_text, int):
            __init__.write_short(use_text)
        else:
            with __init__.write_row(__init__.SHORT, "text"):
                __init__.write_string(use_text)

        __init__.write_byte(0)  # id
        weapon_type = __init__.fetch(obj.get("type", 9))
        __init__.write_byte(weapon_type)
        ability = __init__.bitfield(obj.get("ability", ()))
        weapon_lock = parse_weapon_lock_array(obj.get("weapon_lock", None), table_offset)
        if weapon_type in WEAPONS:
            ability |= 1
        if TOMES_ALWAYS_ATTACK_RES and weapon_type in TOMES:
            ability |= 2
        ability += weapon_lock << 24
        __init__.write_word(ability)
        stat_boosts = parse_stat_boosts(obj.get("stat_boosts", None), table_offset)
        __init__.write_ptr1(stat_boosts)
        effective = parse_effectiveness(obj.get("effective", None), table_offset)
        __init__.write_ptr1(effective)
        uses = obj.get("uses", 1)
        __init__.write_byte(uses)
        __init__.write_byte(obj.get("might", 0))
        __init__.write_byte(obj.get("hit", 0))
        __init__.write_byte(obj.get("weight", 0))
        __init__.write_byte(obj.get("crit", 0))
        __init__.write_byte(parse_range(obj.get("range", 0)))
        __init__.write_short(obj.get("price", obj.get("price_total", 0) / uses))
        __init__.write_byte(parse_rank(obj.get("rank", 0)))
        with table_offset.alloc():
            icon.load_item_icon(path)
        __init__.write_byte(obj.get("use_effect", 0))
        __init__.write_byte(obj.get("damage_effect", 0))
        __init__.write_byte(obj.get("wexp", 1))
        __init__.write_byte(obj.get("debuffs", 1))
        __init__.write_byte(obj.get("23", 1))
        __init__.write_byte(obj.get("skill", 1))

