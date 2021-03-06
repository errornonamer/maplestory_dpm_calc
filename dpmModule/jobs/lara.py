from functools import partial
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


class ElementalSoulStateWrapper(core.GraphElement):
    def __init__(self):
        super(ElementalSoulStateWrapper, self).__init__("속성 상태")

        self.elements = {
            "water": False,
            "wind": False,
            "fire": False
        }

    def _set_element(self, el: str, new_state: bool):
        self.elements[el] = new_state
        return self._result_object_cache

    def set_element(self, el: str, new_state: bool):
        task = core.Task(self, partial(self._set_element, el, new_state))
        return core.TaskHolder(task, el)


class JobGenerator(ck.JobGenerator):
    def __init__(self, vEhc = None):
        super(JobGenerator, self).__init__(vEhc = vEhc)
        self.jobtype = "INT"
        self.jobname = "라라"
        #todo: 최적 어빌리티 계산
        self.ability_list = Ability_tool.get_ability_set('boss_pdamage', 'crit', 'buff_rem')
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

    # todo: 4차 스킬 구현, 재대로된 값 리턴
    def generate(
        self, vEhc: AbstractVEnhancer, chtr: AbstractCharacter, options: Dict[str, Any]
    ) -> Tuple[DamageSkillWrapper, List[AbstractSkillWrapper]]:

        passive_level = chtr.get_base_modifier().passive_level + self.combat

        # todo: 소환수 정확한 딜레이값 알아내기

        # 1차
        Unknown1stJobAttack = core.DamageSkill("정기 뿌리기", 660, 250, 4).wrap(core.DamageSkillWrapper)
        MountinKid = core.DamageSkill("산 꼬마", 0, (85 + 35) * 0.4, modifier=core.CharacterModifier(boss_pdamage=(105/85) * 100) + 45).wrap(core.DamageSkillWrapper)

        MountinKid.protect_from_running()
        Unknown1stJobAttack.onAfter(MountinKid)

        # 2차
        # 산의 씨앗은 자동 사용으로만 소환한다 가정
        # todo: 산의 씨앗 공격주기 알아내기
        ElementalSoulState = ElementalSoulStateWrapper()

        SetWaterBurst = ElementalSoulState.set_element("water", False)
        SetWindBurst = ElementalSoulState.set_element("wind", False)
        SetFireBurst = ElementalSoulState.set_element("fire", False)

        SetWaterConsume = ElementalSoulState.set_element("water", True)
        SetWindConsume = ElementalSoulState.set_element("wind", True)
        SetFireConsume = ElementalSoulState.set_element("fire", True)

        VeinBurst = core.BuffSkill("용맥 분출", 0, 0, cooltime=0.3*1000).wrap(core.BuffSkillWrapper)
        VeinBurstWater = core.SummonSkill("분출 : 너울이는 강", 450, (8/16) * 1000, 205 + 105, 4, 16*1000, cooltime=0.3*1000, rem=True).wrap(core.SummonSkillWrapper)
        VeinBurstWind = core.SummonSkill("분출 : 들개바람", 450, (5/16) * 1000, 65 + 105, 5, 16*1000, cooltime=0.3*1000, rem=True).wrap(core.SummonSkillWrapper)
        VeinBurstFire = core.DamageSkill("분출 : 해돋이 우물", 450, 110 + 72, 6, cooltime=0.3*1000).wrap(core.DamageSkillWrapper)
        VeinBurstFirePallet = core.SummonSkill("분출 : 해돋이 우물 (화산탄)", 0, (5/16) * 1000, 72, 3, 16*1000, 0, rem=True).wrap(core.SummonSkillWrapper)
        VeinBurstFireCarpet = core.SummonSkill("분출 : 해돋이 우물 (장판)", 0, 1000, 82, 1, 16*1000, 0, rem=True).wrap(core.SummonSkillWrapper)
        MountinSeed = core.SummonSkill("산의 씨앗", 0, 500, 55, 1 * 4, 10*1000).wrap(core.SummonSkillWrapper)

        VeinBurstWaterOpt = core.OptionalElement(lambda: VeinBurst.is_available(), VeinBurstWater)
        VeinBurstWindOpt = core.OptionalElement(lambda: VeinBurst.is_available(), VeinBurstWind)
        VeinBurstFireOpt = core.OptionalElement(lambda: VeinBurst.is_available(), VeinBurstFire)

        VeinBurstWater.protect_from_running()
        VeinBurstWind.protect_from_running()
        VeinBurstFire.protect_from_running()
        VeinBurstFirePallet.protect_from_running()
        VeinBurstFireCarpet.protect_from_running()
        MountinSeed.protect_from_running()

        VeinBurstWater.onAfters([VeinBurst, MountinSeed])
        VeinBurstWind.onAfters([VeinBurst, MountinSeed])
        VeinBurstFire.onAfters([VeinBurst, MountinSeed, VeinBurstFirePallet, VeinBurstFireCarpet])

        # 3차
        # 물, 바람 발현 스킬은 데미지에 영향을 주지 않음
        # 잠 깨우기는 항상 최소 개수만큼 생성된다고 가정
        VeinManifestationFire = core.BuffSkill("발현 : 햇살 가득 안은 터", 690, 60*1000, cooltime=60*1000, pdamage=15).wrap(core.BuffSkillWrapper)
        VeinAwakening = core.DamageSkill("잠 깨우기", 720, 105 * (1 - (0.4 * 6 / 7)), 4 * 7, 11).wrap(core.DamageSkillWrapper)
        VeinTeleport = core.DamageSkill("용맥의 자취", 120, 500, 2, cooltime=6*1000).wrap(core.DamageSkillWrapper)
        VeinCry = core.BuffSkill("용맥의 메아리", 0, 20*1000, pdamage_indep=5, rem=True).wrap(core.BuffSkillWrapper)

        VeinCry.protect_from_running()
        VeinBurstWater.onAfter(VeinCry)
        VeinBurstWind.onAfter(VeinCry)
        VeinBurstFire.onAfter(VeinCry)
        VeinManifestationFire.onAfter(VeinCry)
        VeinAwakening.onAfter(VeinCry)

        # 4차
        # todo: 동일 속성 분출/흡수 동시에 불가능 조건 구현
        VeinConsume = core.BuffSkill("용맥 흡수", 0, 0, 0.3*1000).wrap(core.BuffSkillWrapper)

        VeinConsumeWater = core.BuffSkill("흡수 : 강 웅덩이 물벼락", 0, 45*1000, cooltime=2.5*1000).wrap(core.BuffSkillWrapper)
        VeinConsumeWind = core.BuffSkill("흡수 : 소소리 바람", 0, 45 * 1000, cooltime=2.5*1000).wrap(core.BuffSkillWrapper)
        VeinConsumeFire = core.BuffSkill("흡수 : 햇빛 맹아리", 0, 45 * 1000, cooltime=2.5*1000).wrap(core.BuffSkillWrapper)

        VeinConsumeWater.protect_from_running()
        VeinConsumeWind.protect_from_running()
        VeinConsumeFire.protect_from_running()

        VeinConsumeWater.onAfters([VeinConsume, VeinCry])
        VeinConsumeWind.onAfters([VeinConsume, VeinCry])
        VeinConsumeFire.onAfters([VeinConsume, VeinCry])

        VeinConsumeWaterOpt = core.OptionalElement(lambda: VeinConsume.is_available(), VeinConsumeWater)
        VeinConsumeWindOpt = core.OptionalElement(lambda: VeinConsume.is_available(), VeinConsumeWind)
        VeinConsumeFireOpt = core.OptionalElement(lambda: VeinConsume.is_available(), VeinConsumeFire)

        VeinConsumeWaterAttack = core.DamageSkill("흡수 : 강 웅덩이 물벼락 (공격)", 2500, 450, 6).wrap(core.DamageSkillWrapper)
        VeinConsumeWindAttack = core.DamageSkill("흡수 : 소소리 바람 (공격)", 2500, 195, 2).wrap(core.DamageSkillWrapper)
        VeinConsumeFireAttack = core.DamageSkill("흡수 : 햇빛 맹아리 (공격)", 2500, 180, 6).wrap(core.DamageSkillWrapper)

        VeinConsumeWaterAttack.protect_from_running()
        VeinConsumeWindAttack.protect_from_running()
        VeinConsumeFireAttack.protect_from_running()

        VeinConsumeWaterAttackOpt = core.OptionalElement(lambda: VeinConsumeWater.is_active() and VeinConsumeWaterAttack.is_available(), VeinConsumeWaterAttack)
        VeinConsumeWindAttackOpt = core.OptionalElement(lambda: VeinConsumeWind.is_active() and VeinConsumeWindAttack.is_available(), VeinConsumeWindAttack)
        VeinConsumeFireAttackOpt = core.OptionalElement(lambda: VeinConsumeFire.is_active() and VeinConsumeFireAttack.is_available(), VeinConsumeFireAttack)

        Unknown1stJobAttack.onAfters([VeinConsumeWaterAttackOpt, VeinConsumeWindAttackOpt, VeinConsumeFireAttackOpt])

        return VeinAwakening, []

