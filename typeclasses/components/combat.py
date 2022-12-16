from typing import TYPE_CHECKING
import random
import inflect
from dataclasses import dataclass, field, fields, is_dataclass
from typeclasses.objects import Object
import evennia.utils as utils
from world.rules import make_context

p = inflect.engine()

DEFAULT_ATTACK_MSG = {
    "bullet": {
        "invuln": "Bullets glance harmlessly off {defender}!",
        "hit": "{defender} staggers under the flurry of bullets.",
        "crit": "Blood spurts uncontrollably from newly-apportioned wounds!",
    },
    "fusion": {
        "hit": "Bolts of multicolored plasma strike {defender}'s armor.",
        "crit": "Molten matter fuses to flesh amidst screams of agony!",
    },
}


@dataclass
class StatContext:
    base: int | float = 0
    bonus: int | float = 0
    total: int | float = 0


@dataclass
class DamageContext:
    amount: int | float = 0
    modified: int | float = 0


@dataclass
class AttackContext:
    div: int | float
    hit: StatContext = field(default_factory=StatContext)
    dodge: StatContext = field(default_factory=StatContext)
    damage: DamageContext = field(default_factory=DamageContext)
    isHit: bool = False
    isCrit: bool = False


@dataclass
class CombatContext:
    attacker: Object = None
    defender: Object = None
    weapon: Object = None
    attacks: list[AttackContext] = field(default_factory=list)
    total: int | float = 0
    element: str = "neutral"
    overkill: int | float = 0


class CombatHandler(object):
    owner = None

    def __init__(self, owner) -> None:
        self.owner = owner

    @property
    def hp(self):
        return self.owner.db.hp

    @hp.setter
    def hp(self, value):
        self.owner.db.hp = value

    @property
    def maxhp(self):
        return self.owner.maxhp

    @property
    def buffs(self):
        return self.owner.buffs

    def deflect(self, damage, raw=False):
        """Returns damage modified by armor, buffs, and other normal combat modifiers"""

        # calc damage
        _d = damage
        if not raw:
            _d = self.buffs.check(_d, "injury")
        return _d

    def injure(
        self,
        damage: int | float,
        combat: CombatContext = None,
        attacker: Object = None,
        element: str = "neutral",
        loud: bool = True,
        event: bool = True,
    ):
        """
        Applies damage. Affected by "injury" buffs.

        Args:
            damage: Damage to take
            loud:   Trigger a damage event (default: True)
            raw:    Is this "raw" damage (unmodified by buffs)?
            context:    Context to update
        """

        # calculate damage
        damage = self.owner.check_buffs(damage, "injury")
        taken = round(damage) if damage < self.hp else self.hp
        overkill = max(damage - taken, 0)

        # basic damage context in case there's no active combat
        basic = {
            "attacker": attacker,
            "defender": self.owner,
            "total": taken,
            "element": element,
            "overkill": overkill,
        }

        # context updating and dict conversion (or basic values)
        if combat:
            combat.total, combat.overkill = taken, overkill
        _c = (
            dict((field.name, getattr(combat, field.name)) for field in fields(combat))
            if combat
            else basic
        )

        # deal damage
        self.hp = max(self.hp - taken, 0)
        if loud:
            self.owner.msg("  ... You take %i damage!" % int(taken))

        # fire injury event
        if event:
            self.owner.events.publish("injury", attacker, context=_c)

        # If you are out of life, you are out of luck
        was_kill = self.hp <= 0
        if was_kill:
            self.die()
            self.owner.events.publish("death", attacker, context=_c)

    def die(self, context=None):
        """Die! Marks you as dead."""
        context = make_context(context)
        self.owner.tags.clear(category="combat")
        self.owner.tags.add("dead", category="combat")

    def heal(self, heal: int, msg=None) -> int:
        """Heals you.

        Args:
            heal:   The amount you want to heal for (will be converted to an int)
        """
        self.hp = min(self.hp + heal, self.maxhp)
        self.owner.msg("You healed by %i!" % heal)

    def opposed_hit(self, acc=0.0, eva=0.0, crit=2.0) -> AttackContext:
        """
        Performs an "opposed hit roll". An example of this would be an accuracy
        vs evasion roll, or an awareness vs spread roll. Each roll is
        d100 + random(acc/eva), and a hit is made if the hit value is higher.

        Args:
            acc:    The attacker's accuracy modifier.(default: 0)
            eva:    The defender's evasion modifier. (default: 0)
            crit:   The attacker's crit modifier (default: 2)
            context:    (optional) The context dictionary you wish to update with this method's values

        Returns a context dictionary updated with the following values:
            hit/dodge:  nested dictionary of {base, bonus, total}
            is_hit:     if this was a hit
            hit_div:    hit total divided by dodge total
        """
        # Roll two d100s
        _hit = int(random.random() * 100)
        _dodge = int(random.random() * 100)

        # Add random(accuracy) to the relevant values
        accuracy = acc * random.random()
        evasion = eva * random.random()

        _h = {"base": _hit, "bonus": accuracy, "total": round(_hit + accuracy)}
        _d = {"base": _dodge, "bonus": evasion, "total": round(_dodge + evasion)}
        hit, dodge = StatContext(**_h), StatContext(**_d)

        update = {
            "hit": hit,
            "dodge": dodge,
            "div": (_hit + accuracy) / (_dodge + evasion),
            "isHit": (_hit + accuracy) > (_dodge + evasion),
            "isCrit": _hit > _dodge * crit,
        }

        # Generate the AttackContext
        context: AttackContext = AttackContext(**update)
        return context

    def weapon_attack(self, weapon, defender: Object):
        """
        Performs an attack against a defender, according to the weapon's various stats

        Args:
            defender:   The target you are attacking
            context:    (optional) The context you want to feed into the attack method
        """
        # initial context
        attacker: Object = self.owner
        _basics = {
            "attacker": attacker,
            "defender": defender,
            "weapon": weapon,
            "attacks": [],
            "element": "neutral",
        }
        combat: CombatContext = CombatContext(**_basics)

        # variable assignments
        _acc = attacker.buffs.check(weapon.accuracy, "accuracy")
        _eva = defender.evasion

        # Message queues, for sending out after the function completes
        msg_queue = []
        cast_queue = []

        # variable assignment
        _cdict = dict(
            (field.name, getattr(combat, field.name)) for field in fields(combat)
        )
        _crit = weapon.crit
        base_msg = weapon.db.msg["self"].format(**_cdict)
        room_msg = weapon.db.msg["attack"].format(**_cdict)

        attacker.msg(base_msg)
        attacker.location.msg_contents(room_msg, exclude=attacker)
        _shots = weapon.shots
        was_hit = False
        was_crit = False
        dmg_total = 0

        for x in range(max(1, _shots)):
            # roll to hit and update variables
            attack: AttackContext = self.opposed_hit(_acc, _eva, _crit)

            if x == 0:
                roll_msg = "  HIT: +{hit} vs EVA: +{dodge}"
                attacker.msg(
                    roll_msg.format(hit=attack.hit.total, dodge=attack.dodge.total)
                )

            if attack.isHit:
                # precision check
                was_hit = True
                attack.damage.amount = weapon.randomized_damage

                # crit multiply
                if attack.isCrit:
                    was_crit = True
                    _prec = attacker.buffs.check(weapon.precision, "precision")
                    _critdmg = attack.damage.amount * _prec
                    attack.damage.amount = _critdmg

                attacker.events.publish("hit", weapon, combat)

                # damage modification
                attack.damage.modified = defender.combat.deflect(attack.damage.amount)
                combat.attacks.append(attack)

            else:
                if x == 0:
                    attacker.location.msg_contents("    ... Miss!")
                    attacker.events.publish("miss", weapon, combat)
                break

        # outro
        if was_hit:

            # damage messaging setup
            indent = "    "
            prefix = "... "
            message = "{dmg} damage!"
            dmglist = ""

            for atk in combat.attacks:
                dmg = atk.damage.modified
                if atk.damage.modified <= 0:
                    dmg = "no"

                # damage application
                dmglist += message.format(dmg=dmg)
                combat.total += atk.damage.modified

            # attacks message
            attacker.location.msg_contents(indent + prefix + dmglist)

            # apply total damage buffs
            combat.total = weapon.buffs.check(combat.total, "total_damage")

            # total damage message
            prefix = "  = "
            message = "{dmg} total damage!".format(dmg=combat.total)
            if combat.total:
                attacker.location.msg_contents(indent + prefix + message)

            # hit messaging
            hit_msg = DEFAULT_ATTACK_MSG["bullet"]["hit"]
            crit_msg = DEFAULT_ATTACK_MSG["bullet"]["crit"]
            invuln_msg = DEFAULT_ATTACK_MSG["bullet"]["invuln"]
            _msgH = hit_msg.format(**_cdict).capitalize()
            _msgC = crit_msg.format(**_cdict).capitalize()
            _msgI = invuln_msg.format(**_cdict).capitalize()

            if not combat.total:
                attacker.location.msg_contents("    " + _msgI)
            elif was_crit:
                attacker.location.msg_contents("    " + _msgC)
            else:
                attacker.location.msg_contents("    " + _msgH)

            defender.combat.injure(combat.total, combat)

        attacker.location.msg_contents("|n\n")
