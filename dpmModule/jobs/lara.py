from functools import partial
from math import ceil
from typing import Optional, Tuple, List, Dict, Any

from ..character.characterKernel import AbstractCharacter
from ..kernel import core
from ..character import characterKernel as ck
from ..kernel.abstract import AbstractVEnhancer
from ..kernel.core import AbstractSkillWrapper, DamageSkillWrapper, InformedCharacterModifier
from ..status.ability import Ability_tool
from ..execution.rules import RuleSet, MutualRule, InactiveRule, ConcurrentRunRule, ReservationRule, ConditionRule
from . import globalSkill
from .jobbranch import magicians
from . import jobutils

# todo: 모든 스킬 변수 이름 영어 번역명으로 번경


class CancelableBuffWrapper(core.BuffSkillWrapper):
    def __init__(self, skill):
        super(CancelableBuffWrapper, self).__init__(skill)

    def _cancel_buff(self):
        return self.set_disabled()

    def cancel_buff(self):
        task = core.Task(self, partial(self._cancel_buff))
        return core.TaskHolder(task)


class CancelableSummonWrapper(core.SummonSkillWrapper):
    def __init__(self, skill, modifier):
        super(CancelableSummonWrapper, self).__init__(skill, modifier)

    def _cancel_summon(self):
        return self.set_disabled()

    def cancel_summon(self):
        task = core.Task(self, partial(self._cancel_summon))
        return core.TaskHolder(task)


class JobGenerator(ck.JobGenerator):
    def __init__(self):
        super(JobGenerator, self).__init__()

        self.jobtype = "INT"
        self.jobname = "라라"
        self.ability_list = Ability_tool.get_ability_set('boss_pdamage', 'buff_rem', 'mess')
        self.preEmptiveSkills = 1

    def get_passive_skill_list(
        self, vEhc, chtr: AbstractCharacter, options: Dict[str, Any]
    ) -> List[InformedCharacterModifier]:
        passive_level = chtr.get_base_modifier().passive_level + self.combat
        SpiritAffinity = core.InformedCharacterModifier("정령친화", summon_rem=10)
        WandMastery = core.InformedCharacterModifier("지팡이 숙련", att=35)
        IntFitness = core.InformedCharacterModifier("신체 단련", int=40)
        UnknownPassive1 = core.InformedCharacterModifier("무구", pdamage=20, crit=20)
        AdvancedWandMastery = core.InformedCharacterModifier("고급 지팡이 숙련", pdamage_indep=30, att=50)
        UnknownPassive2 = core.InformedCharacterModifier("혜안", crit=20, crit_damage=20, pdamage_indep=30, armor_ignore=40)
        UnknownPassive3 = core.InformedCharacterModifier("유유", att=50)

        return [SpiritAffinity, WandMastery, IntFitness, UnknownPassive1, AdvancedWandMastery, UnknownPassive2, UnknownPassive3]

    def get_not_implied_skill_list(
        self, vEhc, chtr: AbstractCharacter, options: Dict[str, Any]
    ) -> List[InformedCharacterModifier]:
        passive_level = chtr.get_base_modifier().passive_level + self.combat
        Mastery = core.InformedCharacterModifier("숙련도", mastery=95 + ceil(passive_level / 2))
        return [Mastery]

    #def get_ruleset(self) -> Optional[RuleSet]:    todo: 최적 딜사이클 계산

    def generate(
        self, vEhc: AbstractVEnhancer, chtr: AbstractCharacter, options: Dict[str, Any]
    ) -> Tuple[DamageSkillWrapper, List[AbstractSkillWrapper]]:
        passive_level = chtr.get_base_modifier().passive_level + self.combat

        # todo: 소환수 정확한 딜레이값 알아내기
        # todo: 강화코어 적용

        # 1차
        LaraAttack = core.DamageSkill("정기 뿌리기", 660, 250, 4).wrap(core.DamageSkillWrapper)
        MountinKid = core.DamageSkill("산 꼬마", 0, (85 + 35) * 0.4, modifier=core.CharacterModifier(boss_pdamage=(105/85) * 100) + 45).wrap(core.DamageSkillWrapper)

        MountinKid.protect_from_running()
        LaraAttack.onAfter(MountinKid)

        # 2차
        # 산의 씨앗은 자동 사용으로만 소환한다 가정
        # todo: 산의 씨앗 공격주기 알아내기
        Eruption = core.BuffSkill("용맥 분출", 0, 0, cooltime=300).wrap(core.BuffSkillWrapper)
        EruptionRiver = core.SummonSkill("분출 : 너울이는 강", 450, (8/16) * 1000, 205 + 105, 4, 16*1000, cooltime=-1).wrap(CancelableSummonWrapper)
        EruptionWind = core.SummonSkill("분출 : 들개바람", 450, (5/16) * 1000, 65 + 105, 5, 16*1000, cooltime=-1).wrap(CancelableSummonWrapper)
        EruptionSun = core.DamageSkill("분출 : 해돋이 우물", 450, 110 + 72, 6, cooltime=-1).wrap(core.DamageSkillWrapper)
        EruptionSunPallet = core.SummonSkill("분출 : 해돋이 우물 (화산탄)", 0, (5/16) * 1000, 72, 1, 16*1000, 0, cooltime=-1).wrap(CancelableSummonWrapper)
        EruptionSunPallet_2 = core.SummonSkill("분출 : 해돋이 우물 (화산탄 후속타)", 0, (5 / 16) * 1000, 72 * 0.9, 2, 16*1000, 0, cooltime=-1).wrap(CancelableSummonWrapper)
        EruptionSunCarpet = core.SummonSkill("분출 : 해돋이 우물 (장판)", 0, 1000, 82, 1, 16*1000, 0, cooltime=-1).wrap(CancelableSummonWrapper)
        EruptionSunDot = core.DotSkill("분출 : 해돋이 우물 (도트)", 0, 1000, 110, 1, 8000, cooltime=-1).wrap(core.DotSkillWrapper)
        Planting = core.StackableSummonSkillWrapper(
            core.SummonSkill("산의 씨앗", 0, 500, 55, 1 * 4, 10*1000, cooltime=-1),
            max_stack=4
        )

        EruptionRiverOpt = core.OptionalElement(lambda: Eruption.is_available(), EruptionRiver)
        EruptionWindOpt = core.OptionalElement(lambda: Eruption.is_available(), EruptionWind)
        EruptionSunOpt = core.OptionalElement(lambda: Eruption.is_available(), EruptionSun)

        EruptionRiver.protect_from_running()
        EruptionWind.protect_from_running()
        EruptionSun.protect_from_running()
        EruptionSunPallet.protect_from_running()
        EruptionSunPallet_2.protect_from_running()
        EruptionSunCarpet.protect_from_running()
        EruptionSunDot.protect_from_running()
        Planting.protect_from_running()

        EruptionRiver.onAfters([Eruption, Planting])
        EruptionWind.onAfters([Eruption, Planting])
        EruptionSun.onAfters([Eruption, Planting, EruptionSunPallet, EruptionSunPallet_2, EruptionSunCarpet, EruptionSunDot])

        # 3차
        # 물, 바람 발현 스킬은 데미지에 영향을 주지 않음
        # 잠 깨우기는 항상 최소 개수만큼 생성된다고 가정
        ExpressionSun = core.BuffSkill("발현 : 햇살 가득 안은 터", 690, 60*1000, cooltime=60000, pdamage=15).wrap(core.BuffSkillWrapper)
        RoughEruption = core.DamageSkill("잠 깨우기", 720, 105, 4, cooltime=11000).wrap(core.DamageSkillWrapper)
        RoughEruption_2 = core.DamageSkill("잠 깨우기 (후속타)", 0, 105 * 0.6, 4 * 6, cooltime=-1).wrap(core.DamageSkillWrapper)
        Teleport = core.DamageSkill("용맥의 자취", 120, 500, 2, cooltime=6000).wrap(core.DamageSkillWrapper)

        RoughEruption_2.protect_from_running()
        RoughEruption.onAfter(RoughEruption_2)

        # 4차
        Absorption = core.BuffSkill("용맥 흡수", 0, 0, 0.3*1000).wrap(core.BuffSkillWrapper)

        AbsorptionRiver = core.BuffSkill("흡수 : 강 웅덩이 물벼락", 0, 45*1000, cooltime=-1).wrap(CancelableBuffWrapper)
        AbsorptionWind = core.BuffSkill("흡수 : 소소리 바람", 0, 45 * 1000, cooltime=-1).wrap(CancelableBuffWrapper)
        AbsorptionSun = core.BuffSkill("흡수 : 햇빛 맹아리", 0, 45 * 1000, cooltime=-1).wrap(CancelableBuffWrapper)

        AbsorptionRiver.protect_from_running()
        AbsorptionWind.protect_from_running()
        AbsorptionSun.protect_from_running()

        CancelEruptionRiver = EruptionRiver.cancel_summon()
        CancelEruptionWind = EruptionWind.cancel_summon()
        CancelEruptionSun = EruptionSunCarpet.cancel_summon()
        CancelEruptionSun.onAfter(EruptionSunPallet.cancel_summon())

        CancelAbsorptionRiver = AbsorptionRiver.cancel_buff()
        CancelAbsorptionWind = AbsorptionWind.cancel_buff()
        CancelAbsorptionSun = AbsorptionSun.cancel_buff()

        AbsorptionRiver.onAfters([Absorption, CancelEruptionRiver])
        AbsorptionWind.onAfters([Absorption, CancelEruptionWind])
        AbsorptionSun.onAfters([Absorption, CancelEruptionSun])

        EruptionRiver.onAfter(CancelAbsorptionRiver)
        EruptionWind.onAfter(CancelAbsorptionWind)
        EruptionSun.onAfter(CancelAbsorptionSun)

        AbsorptionRiverOpt = core.OptionalElement(lambda: Absorption.is_available(), AbsorptionRiver)
        AbsorptionWindOpt = core.OptionalElement(lambda: Absorption.is_available(), AbsorptionWind)
        AbsorptionSunOpt = core.OptionalElement(lambda: Absorption.is_available(), AbsorptionSun)

        AbsorptionRiverAttack = core.DamageSkill("흡수 : 강 웅덩이 물벼락 (공격)", 2500, 450, 6, cooltime=2500).wrap(core.DamageSkillWrapper)
        AbsorptionWindAttack = core.DamageSkill("흡수 : 소소리 바람 (공격)", 2500, 195, 2, cooltime=2500).wrap(core.DamageSkillWrapper)
        AbsorptionSunAttack = core.DamageSkill("흡수 : 햇빛 맹아리 (공격)", 2500, 180, 6, cooltime=2500).wrap(core.DamageSkillWrapper)

        AbsorptionRiverAttack.protect_from_running()
        AbsorptionWindAttack.protect_from_running()
        AbsorptionSunAttack.protect_from_running()

        AbsorptionRiverAttackOpt = core.OptionalElement(lambda: AbsorptionRiver.is_active() and AbsorptionRiverAttack.is_available(), AbsorptionRiverAttack)
        AbsorptionWindAttackOpt = core.OptionalElement(lambda: AbsorptionWind.is_active() and AbsorptionWindAttack.is_available(), AbsorptionWindAttack)
        AbsorptionSunAttackOpt = core.OptionalElement(lambda: AbsorptionSun.is_active() and AbsorptionSunAttack.is_available(), AbsorptionSunAttack)

        LaraAttack.onAfters([AbsorptionRiverAttackOpt, AbsorptionWindAttackOpt, AbsorptionSunAttackOpt])

        # 하이퍼
        HomeOfSpirits = core.BuffSkill("아름드리 나무", 660, 30, cooltime=180000, armor_ignore=15, boss_pdamage=50, crit_damage=10).wrap(core.BuffSkillWrapper)

        # 5차
        OverloadMana = magicians.OverloadManaBuilder(vEhc, 0, 0)
        AnimaGoddessBless = core.BuffSkill("그란디스 여신의 축복 (아니마)", 0, 40 * 1000, cooltime=240000, red=True,
                                           pdamage=10 + vEhc.getV(0, 0)).isV(vEhc, 0, 0).wrap(core.BuffSkillWrapper)
        VeinMassAwakening = core.DamageSkill("큰 기지개", 870, 400 + vEhc.getV(0, 0) * 16, 5, cooltime=60000).wrap(core.DamageSkillWrapper)
        VeinMassAwakening_2 = core.DamageSkill("큰 기지개 (후속타)", 0, (400 + vEhc.getV(0, 0) * 16) * 0.7, 6 * 5).isV(vEhc, 0, 0).wrap(core.DamageSkillWrapper)
        CombinationBlow = core.DamageSkill("해 산 강 바람", 840, 675 + vEhc.getV(0, 0) * 27, 10*3, cooltime=180000).isV(vEhc, 0, 0).wrap(core.DamageSkillWrapper)
        CombinationBlow_2 = core.DamageSkill("해 산 강 바람 (폭발)", 0, 750 + vEhc.getV(0, 0) * 30, 15*7).isV(vEhc, 0, 0).wrap(core.DamageSkillWrapper)
        AdvancedLaraAttack = core.DamageSkill("용솟음치는 정기", 630, 425 + vEhc.getV(0, 0) * 17, 8*5, cooltime=20000).isV(vEhc, 0, 0).wrap(core.DamageSkillWrapper)
        BurstUp = core.SummonSkill("산등성이 굽이굽이", 960, (20/30) * 1000, 325 + vEhc.getV(0, 0) * 13, 4*3, 30000, cooltime=60000).isV(vEhc, 0, 0).wrap(core.SummonSkillWrapper)

        MirrorBreak, MirrorSpider = globalSkill.SpiderInMirrorBuilder(vEhc, 0, 0)

        VeinCry = core.BuffSkill("용맥의 메아리", 0, 20000, pdamage_indep=5, rem=True, cooltime=-1).wrap(CancelableBuffWrapper)
        VeinCryBuffed = core.BuffSkill("용맥의 메아리 (그여축)", 0, 20000, pdamage_indep=10, rem=True, cooltime=-1).wrap(CancelableBuffWrapper)

        CancelVeinCry = VeinCry.cancel_buff()
        CancelVeinCryBuffed = VeinCryBuffed.cancel_buff()

        VeinCry.protect_from_running()
        VeinCryBuffed.protect_from_running()

        VeinCry.onAfter(CancelVeinCryBuffed)
        VeinCryBuffed.onAfter(CancelVeinCry)

        VeinCryOpt = core.OptionalElement(lambda: AnimaGoddessBless.is_active(), VeinCryBuffed, fail=VeinCry)

        VeinMassAwakening_2.protect_from_running()
        CombinationBlow_2.protect_from_running()
        EruptionRiver.onAfter(VeinCryOpt)
        EruptionWind.onAfter(VeinCryOpt)
        EruptionSun.onAfter(VeinCryOpt)
        ExpressionSun.onAfter(VeinCryOpt)
        RoughEruption.onAfter(VeinCryOpt)
        AbsorptionRiver.onAfter(VeinCryOpt)
        AbsorptionWind.onAfter(VeinCryOpt)
        AbsorptionSun.onAfter(VeinCryOpt)
        VeinMassAwakening.onAfters([VeinCryOpt, VeinMassAwakening_2])
        CombinationBlow.onAfter(CombinationBlow_2)

        return (
            LaraAttack,
            [
                globalSkill.maple_heros(chtr.level, name="아니마의 용사", combat_level=self.combat),
                globalSkill.useful_sharp_eyes(),
                globalSkill.useful_combat_orders(),
                ExpressionSun,
                HomeOfSpirits,
                AnimaGoddessBless,
                VeinMassAwakening,
                CombinationBlow,
                AdvancedLaraAttack,
                BurstUp,
                globalSkill.soul_contract()
            ]
            + [EruptionRiver, EruptionWind, EruptionSunCarpet, EruptionSunPallet, EruptionSunPallet_2, EruptionSunDot, Planting]
            + [EruptionRiverOpt, EruptionWindOpt, EruptionSunOpt, AbsorptionRiverOpt, AbsorptionWindOpt, AbsorptionSunOpt, MirrorBreak, MirrorSpider]
            + [LaraAttack]
        )

