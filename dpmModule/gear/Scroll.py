import math
from collections import defaultdict
from typing import Dict, DefaultDict

from .Gear import Gear
from .GearPropType import GearPropType
from .GearType import GearType

PropMap = DefaultDict[GearPropType, int]


class Scroll:
    def __init__(self, stat: PropMap = None, name: str = None,
                 bonus_pad_on_fourth: bool = False, bonus_mad_on_fourth: bool = False):
        self.stat: PropMap = stat or defaultdict(int)
        self.name: str = name
        self.bonus_pad_on_fourth: bool = bonus_pad_on_fourth
        self.bonus_mad_on_fourth: bool = bonus_mad_on_fourth

    @staticmethod
    def create_from_dict(stat: Dict[GearPropType, int], name: str = None):
        """
        Create scroll with given stat and name.
        :param stat: Dict with stats.
        :param name: Name of the scroll.
        :return: Scroll with given stat and name.
        """
        return Scroll(defaultdict(int, stat), name)

    @staticmethod
    def get_spell_trace_scroll(gear: Gear, probability: int, prop_type: GearPropType):
        """
        Returns corresponding spell trace scroll.
        :param gear: Target gear; req_job, req_level, type are used.
        :param probability: 100 or 70 or 30 or 15
        :param prop_type: Prop type of spell trace scroll.
        :return: Spell trace scroll.
        :raises TypeError: If matching spell trace scroll does not exist for gear.
        """
        if probability != 100 and probability != 70 and probability != 30 and probability != 15:
            raise TypeError('Invalid probability: ' + str(probability))
        if (prop_type != GearPropType.STR and
                prop_type != GearPropType.DEX and
                prop_type != GearPropType.INT and
                prop_type != GearPropType.LUK and
                prop_type != GearPropType.MHP):
            raise TypeError('Invalid prop_type: ' + prop_type.name)

        scroll: Scroll = Scroll()
        req_job: int = gear.req_job
        mad: bool = req_job == 0 or math.floor(req_job / 2) % 2 == 1
        pad: bool = req_job == 0 or not mad
        attack_type = GearPropType.matt if prop_type == GearPropType.INT else GearPropType.att
        gear_type = gear.type
        req_level = gear.req_level
        level_range = 2 if req_level > 110 else (1 if req_level > 70 else 0)

        if Gear.is_weapon(gear_type) or gear_type == GearType.katara:
            if probability == 100:
                data = [[1, 0], [2, 0], [3, 1]]
            elif probability == 70:
                data = [[2, 0], [3, 1], [5, 2]]
            elif probability == 30:
                data = [[3, 1], [5, 2], [7, 3]]
            elif probability == 15:
                data = [[5, 2], [7, 3], [9, 4]]
            attack_value = data[level_range][0]
            stat_value = data[level_range][1] * (50 if prop_type == GearPropType.MHP else 1)
            stat = {prop_type: stat_value, attack_type: attack_value}
            scroll.stat = stat
            return scroll
        elif probability == 15:
            raise TypeError('Invalid probability' + str(probability) + 'for GearType: ' + gear_type.name)
        elif gear_type == GearType.glove:
            if probability == 100:
                data = [0, 1, 1]
            elif probability == 70:
                data = [1, 2, 2]
            elif probability == 30:
                data = [2, 3, 3]
            value = data[level_range]
            # stat = {GearPropType.incPDD: 3} if value == 0 else {attack_type: value}
            stat = {} if value == 0 else {attack_type: value}
            scroll.stat = stat
            return scroll
        elif Gear.is_armor(gear_type):
            if probability == 100:
                data = [[1, 5, 1], [2, 20, 2], [3, 30, 3]]
            elif probability == 70:
                data = [[2, 15, 2], [3, 40, 4], [4, 70, 5]]
            elif probability == 30:
                data = [[3, 30, 4], [5, 70, 7], [7, 120, 10]]
            stat_value = 0 if prop_type == GearPropType.MHP else data[level_range][0]
            mhp_value = data[level_range][1] + (data[level_range][0] * 50 if prop_type == GearPropType.MHP else 0)
            # pdd_value = data[level_range][2]
            # stat = {GearPropType.MHP: mhp_value, GearPropType.incPDD: pdd_value}
            stat = {GearPropType.MHP: mhp_value}
            if stat_value > 0:
                stat[prop_type] = stat_value
            scroll.stat = stat
            scroll.bonus_pad_on_fourth = pad
            scroll.bonus_mad_on_fourth = mad
            return scroll
        elif Gear.is_accessory(gear_type):
            if probability == 100:
                data = [1, 1, 2]
            elif probability == 70:
                data = [2, 2, 3]
            elif probability == 30:
                data = [3, 4, 5]
            value = data[level_range] * (50 if prop_type == GearPropType.MHP else 1)
            stat = {prop_type: value}
            scroll.stat = stat
            scroll.bonus_pad_on_fourth = pad
            scroll.bonus_mad_on_fourth = mad
            return scroll
        elif gear_type == GearType.machine_heart:
            if probability == 100:
                data = [1, 2, 3]
            elif probability == 70:
                data = [2, 3, 5]
            elif probability == 30:
                data = [3, 5, 7]
            value = data[level_range]
            stat = {attack_type: value}
            scroll.stat = stat
            return scroll
        else:
            raise TypeError('Spell trace Scroll does not exist for GearType: ' + gear_type.name)
