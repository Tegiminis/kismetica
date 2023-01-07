from typing import TYPE_CHECKING
import random
import inflect
from dataclasses import dataclass, field, fields, is_dataclass
from components.context import StatContext, congen
from typeclasses.objects import Object
import evennia.utils as utils
from world.rules import verify_context, capitalize

p = inflect.engine()

DEFAULT_TEMP_MSG = {
    "bullet": {
        "invuln": "Bullets glance harmlessly off {defender}!",
    },
    "fusion": {
        "hit": "Bolts of multicolored plasma strike {defender}'s armor.",
        "crit": "Molten matter fuses to flesh amidst screams of agony!",
    },
}

DEFAULT_ATTACK_MSG = "{attacker} shoots {name} at {defender}"
DEFAULT_READY_MSG = "You shoulder your {name}, ready to fire."
DEFAULT_HIT_MSG = "{defender} staggers under the flurry of bullets."
DEFAULT_CRIT_MSG = "Blood spurts uncontrollably from newly-apportioned wounds!"

DEFAULT_DEATH_MSG = "{owner} collapses in a heap!"
DEFAULT_REVIVE_MSG = "{owner} suddenly begins breathing again!"

INDENT = "    "
PREFIX = "..."
NEWLINE = "|n\n"


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
    messaging: dict = field(default_factory=dict)
    is_object: bool = False
    prototype_key: str = ""


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

    @property
    def dead(self):
        return self.owner.tags.has("dead", category="combat")

    def deflect(self, damage, raw=False):
        """Returns damage modified by armor, buffs, and other normal combat modifiers"""

        # calculate damage
        _d = damage

        # apply buffs (flat damage resistance)
        if not raw:
            _d = self.buffs.check(_d, "injury")

        # return damage
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
        if buffcheck:
            damage = self.owner.check_buffs(damage, "injury")
        _hp = int(self.hp)
        taken = round(damage) if damage < _hp else _hp
        overkill = max(damage - taken, 0)

        # context updating and dict conversion (or basic values)
        if context:
            context.taken, context.overkill = taken, overkill
            context = congen([context])
        else:
            context = {
                "attacker": attacker,
                "defender": self.owner,
                "total": damage,
                "taken": taken,
                "element": element,
                "overkill": overkill,
            }

        # deal damage
        self.hp = max(self.hp - taken, 0)
        was_kill = self.hp <= 0
        if loud:
            self.owner.msg("|rYou take {0} damage!|n".format(taken))

        # fire injury event
        if event:
            self.owner.events.publish("injury", attacker, context)

        # no life, no luck
        if was_kill:
            # if this object grants xp, and the attacker can gain it, transfer xp
            gain = self.owner.attributes.get("gain", None)
            xp = attacker.attributes.has("xp")
            if gain and xp:
                attacker.db.xp = min(gain + xp, attacker.limit)

            # die and publish death event
            self.die(context)
            self.owner.events.publish("death", attacker, context)

        # return the combat context
        return CombatContext(**context)

    def die(self, context=None):
        """Die! Marks you as dead."""
        # tag and buff stuff
        self.owner.tags.clear(category="combat")
        self.owner.tags.add("dead", category="combat")
        self.owner.buffs.super_remove(tag="remove_on_death")

        # messaging
        messaging = self.owner.attributes.get("messaging", {})
        message = messaging.get("death", DEFAULT_DEATH_MSG)
        formatted = capitalize(message.format(owner=self.owner))

        # send message and delay revive
        self.owner.location.msg_contents(formatted)
        utils.delay(10, revive, self.owner, persistent=True)

    def revive(self):
        """Revive! You aren't dead anymore!"""
        # tag stuff
        self.owner.tags.clear(category="combat")
        self.owner.db.hp = self.owner.db.maxhp

        # messaging
        rev_msg = self.owner.attributes.get("messaging", {}).get("revive", None)
        if not rev_msg:
            rev_msg = DEFAULT_REVIVE_MSG
        formatted = capitalize(rev_msg.format(owner=self.owner))

        # send revive message
        self.owner.location.msg_contents(formatted)

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
            acc:    (default: 0) The attacker's accuracy modifier.
            eva:    (default: 0) The defender's evasion modifier.
            crit:   (default: 2) The attacker's crit modifier

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

    def weapon_attack(self, weapon: WeaponStats, defender: Object):
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
        evasion = getattr(defender, "evasion", 0)

        # opening damage message formatting
        mapping = congen([combat])
        mapping.update(
            {
                "weapon": weapon.name,
                "attacker": attacker.get_display_name(),
                "defender": defender.get_display_name(),
            }
        )
        room_msg = weapon.messaging.get("attack", DEFAULT_ATTACK_MSG)
        formatted = capitalize(room_msg.format(**mapping))

        # send message
        attacker.location.msg_contents(NEWLINE)
        attacker.location.msg_contents(formatted)

        # attack prep
        shots = int(weapon.shots)
        was_hit = False
        was_crit = False

        # roll to hit based on number of shots
        for x in range(shots):

            # roll to hit and update variables
            attack: AttackContext = self.opposed_hit(
                accuracy_modified, evasion, weapon.crit, weapon.damage
            )

            # if this is the first shot, send the initial hit roll numbers
            if x == 0:
                hitmapping = {"hit": attack.hit.total, "dodge": attack.dodge.total}
                roll_msg = "  HIT: +{hit} vs EVA: +{dodge}"
                formatted = roll_msg.format(**hitmapping)
                attacker.location.msg_contents(formatted)

            # if attack was successful
            if attack.isHit:
                was_hit = True

                # if crit (hit > evasion * crit), multiply damage
                if attack.isCrit:
                    was_crit = True
                    precision_mult = attacker.buffs.check(weapon.mult, "precision")
                    attack.damage *= precision_mult

                # creating combined context dictionary
                context = congen([attack, combat])

                # attacker publishes event
                attacker.events.publish("hit", attacker, context)

                # damage modification
                attack.damage = defender.combat.deflect(attack.damage)
                combat.attacks.append(attack)

        # hit (at least one successful hit)
        if was_hit:

            # damage messaging setup
            message = " {0} damage!"
            dmglist_msg = ""

            # individual attack messages and damage totaling
            for atk in combat.attacks:
                dmg = round(atk.damage)
                if atk.damage <= 0:
                    dmg = "No"
                if atk.isCrit:
                    dmg = "|520" + str(dmg)
                dmglist_msg += message.format(dmg) + "|n"
                combat.total += atk.damage

            # attacks message
            attacker.location.msg_contents(INDENT + PREFIX + dmglist_msg)

            # apply total damage buffs
            weapon_object = attacker.attributes.get("held", None)
            if weapon_object:
                combat.total = weapon_object.buffs.check(combat.total, "total_damage")
            combat.total = attacker.check_buffs(combat.total, "total_damage")

            # total damage message
            TOTAL = "  = "
            message = "{0} total damage!".format(round(combat.total))
            if combat.total:
                attacker.location.msg_contents(INDENT + TOTAL + message)

            # hit messaging
            formatted, msg = "", ""

            mapping = congen([combat])

            if not combat.total:
                msg = DEFAULT_TEMP_MSG["bullet"]["invuln"]
            elif was_crit:
                msg = weapon.messaging.get("crit", DEFAULT_CRIT_MSG)
            else:
                msg = weapon.messaging.get("hit", DEFAULT_HIT_MSG)

            formatted = msg.format(**mapping)
            capitalized = capitalize(formatted)
            attacker.location.msg_contents("|520" + INDENT + capitalized)

            # injury
            defender.combat.injure(combat.total, attacker, context=combat)

        # miss
        else:
            attacker.location.msg_contents(INDENT + PREFIX + " Miss!")
            attacker.events.publish("miss", weapon, combat)


def revive(target):
    """Revive! You aren't dead anymore!"""
    # tag stuff
    target.tags.clear(category="combat")
    target.db.hp = target.db.maxhp

    # messaging
    rev_msg = target.attributes.get("messaging", {}).get("revive", None)
    if not rev_msg:
        rev_msg = DEFAULT_REVIVE_MSG
    formatted = capitalize(rev_msg.format(owner=target))

    # send revive message
    target.location.msg_contents(formatted)
