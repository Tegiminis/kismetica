from typing import TYPE_CHECKING
import random
import inflect
from dataclasses import dataclass, field, fields, is_dataclass
from components.context import StatContext, congen
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
class AttackContext:
    div: int | float
    hit: StatContext = field(default_factory=StatContext)
    dodge: StatContext = field(default_factory=StatContext)
    damage: int | float = 0
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


@dataclass
class WeaponStats:
    name: str = "Template"
    accuracy: int | float = 1.0
    damage: int | float = 10
    crit: int | float = 2.0
    mult: int | float = 2.0
    shots: int | float = 1.0
    cooldown: int | float = 6
    element: str = "neutral"
    msg: str = "{attacker} shoots {defender} with {name}."
    is_object: bool = False


class CombatHandler(object):
    """Performs various combat-related tasks."""

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
        # apply buffs
        if not raw:
            _d = self.buffs.check(_d, "injury")

        return _d

    def injure(
        self,
        damage: int | float,
        attacker: Object = None,
        element: str = "neutral",
        buffcheck: bool = True,
        loud: bool = True,
        event: bool = True,
        context: CombatContext = None,
    ) -> CombatContext:
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
        _hp = int(self.hp)
        taken = round(damage) if damage < _hp else _hp
        overkill = max(damage - taken, 0)

        # context updating and dict conversion (or basic values)
        if context:
            context.total, context.overkill = taken, overkill
            context = congen([context])
        else:
            context = {
                "attacker": attacker,
                "defender": self.owner,
                "total": taken,
                "element": element,
                "overkill": overkill,
            }

        # deal damage
        self.hp = max(self.hp - taken, 0)
        if loud:
            self.owner.msg("  ... You take %i damage!" % int(taken))

        # fire injury event
        if event:
            self.owner.events.publish("injury", attacker, context)

        # If you are out of life, you are out of luck
        was_kill = self.hp <= 0
        if was_kill:
            self.die()
            self.owner.events.publish("death", attacker, context)

        # return the combat context
        return CombatContext(**context)

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
        if not heal:
            return
        self.hp = min(self.hp + heal, self.maxhp)
        self.owner.msg("You healed by %i!" % heal)

    def opposed_hit(self, acc=0.0, eva=0.0, crit=2.0, damage=0) -> AttackContext:
        """
        Performs an "opposed hit roll". An example of this would be an accuracy
        vs evasion roll, or an awareness vs spread roll. Each roll is
        d100 + random(acc/eva), and a hit is made if the hit value is higher.

        Args:
            acc:    The attacker's accuracy modifier.(default: 0)
            eva:    The defender's evasion modifier. (default: 0)
            crit:   The attacker's crit modifier (default: 2)

        Returns an AttackContext object
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
            "damage": damage,
            "isHit": (_hit + accuracy) > (_dodge + evasion),
            "isCrit": _hit > _dodge * crit,
        }

        # Generate the AttackContext
        context: AttackContext = AttackContext(**update)
        return context

    def basic_attack(self, weapon: WeaponStats, defender: Object):
        """
        Performs an attack against a defender, according to the weapon's various stats

        Args:
            weapon:     The weapon you are using. WeaponStats dataclass
            defender:   The target you are attacking
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
        accuracy_modified = attacker.buffs.check(weapon.accuracy, "accuracy")
        evasion = defender.evasion

        # Message queues, for sending out after the function completes
        msg_queue = []
        cast_queue = []

        # opening damage message
        _format = congen([combat])
        _format.update({"name": weapon.name})
        room_msg = weapon.msg.format(**_format)
        attacker.location.msg_contents("|n\n")
        attacker.location.msg_contents(room_msg)
        _shots = weapon.shots
        was_hit = False
        was_crit = False

        for x in range(max(1, _shots)):
            # roll to hit and update variables
            attack: AttackContext = self.opposed_hit(
                accuracy_modified, evasion, weapon.crit, weapon.damage
            )

            if x == 0:
                _format = {"hit": attack.hit.total, "dodge": attack.dodge.total}
                roll_msg = "  HIT: +{hit} vs EVA: +{dodge}"
                attacker.msg(roll_msg.format(**_format))

            if attack.isHit:
                # precision check
                was_hit = True

                # crit multiply
                if attack.isCrit:
                    was_crit = True
                    precision_mult = attacker.buffs.check(weapon.mult, "precision")
                    attack.damage *= precision_mult

                # creating combined context dictionary
                context = congen([attack, combat])

                attacker.events.publish("hit", attacker, context)

                # damage modification
                attack.damage = defender.combat.deflect(attack.damage)
                combat.attacks.append(attack)

        # outro
        if was_hit:

            # damage messaging setup
            indent = "    "
            prefix = "... "
            message = "{dmg} damage!"
            dmglist_msg = ""

            for atk in combat.attacks:
                dmg = atk.damage
                if atk.damage <= 0:
                    dmg = "no"

                # damage application
                dmglist_msg += message.format(dmg=dmg)
                combat.total += atk.damage

            # attacks message
            attacker.location.msg_contents(indent + prefix + dmglist_msg)

            # apply total damage buffs
            weapon_object = attacker.attributes.get("held", None)
            if weapon_object:
                combat.total = weapon_object.buffs.check(combat.total, "total_damage")
            combat.total = attacker.check_buffs(combat.total, "total_damage")

            # total damage message
            prefix = "  = "
            message = "{dmg} total damage!".format(dmg=combat.total)
            if combat.total:
                attacker.location.msg_contents(indent + prefix + message)

            _format = congen([combat])

            # hit messaging
            hit_msg = DEFAULT_ATTACK_MSG["bullet"]["hit"]
            crit_msg = DEFAULT_ATTACK_MSG["bullet"]["crit"]
            invuln_msg = DEFAULT_ATTACK_MSG["bullet"]["invuln"]
            _msgH = hit_msg.format(**_format).capitalize()
            _msgC = crit_msg.format(**_format).capitalize()
            _msgI = invuln_msg.format(**_format).capitalize()

            if not combat.total:
                attacker.location.msg_contents("    " + _msgI)
            elif was_crit:
                attacker.location.msg_contents("    " + _msgC)
            else:
                attacker.location.msg_contents("    " + _msgH)

            defender.combat.injure(combat.total, context=combat)
        else:
            attacker.location.msg_contents("    ... Miss!")
            attacker.events.publish("miss", weapon, combat)

        attacker.location.msg_contents("|n\n")
