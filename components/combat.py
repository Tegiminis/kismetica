from typing import TYPE_CHECKING
import random
import inflect
from dataclasses import dataclass, field, fields, is_dataclass
from components.context import StatContext, congen
from components.events import GameEvent
from typeclasses.objects import Object
import evennia.utils as utils
from world.rules import verify_context, capitalize

p = inflect.engine()

DEFAULT_TEMP_MSG = {
    "bullet": {
        "invuln": "Bullets glance harmlessly off {target}!",
    },
    "fusion": {
        "hit": "Bolts of multicolored plasma strike {target}'s armor.",
        "crit": "Molten matter fuses to flesh amidst screams of agony!",
    },
}

DEFAULT_ATTACK_MSG = "{attacker} shoots {weapon} at {target}"
DEFAULT_READY_MSG = "You shoulder your {weapon}, ready to fire."
DEFAULT_HIT_MSG = "{target} staggers under the flurry of bullets."
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
    eva: StatContext = field(default_factory=StatContext)
    damage: int | float = 0
    deflected: int | float = 0
    isHit: bool = False
    isCrit: bool = False


@dataclass
class CombatContext:
    attacker: Object = None
    target: Object = None
    weapon: Object = None
    attacks: list[AttackContext] = field(default_factory=list)
    damage: int | float = 0
    taken: int | float = 0
    element: str = "neutral"
    overkill: int | float = 0


@dataclass
class OffenseStats:
    accuracy: int | float = 1.0
    opposing: str = "evasion"
    damage: int | float = 10
    crit: int | float = 2.0
    mult: int | float = 2.0


@dataclass
class WeaponStats:
    weapon: str = "Template"
    accuracy: int | float = 1.0
    damage: int | float = 10
    crit: int | float = 2.0
    mult: int | float = 2.0
    shots: int | float = 1.0
    cooldown: int | float = 6
    element: str = "neutral"
    messaging: dict = field(default_factory=dict)
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

    @property
    def attackers(self) -> list:
        _a = self.owner.ndb.attackers
        if _a:
            return _a
        else:
            return None

    def end_combat(self):
        """Ends combat on this object"""
        self.owner.tags.clear(category="combat")
        self.owner.ndb.attackers = []

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
        is_event: bool = True,
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

        # setting up the game event tags
        defender_tags = []
        attacker_tags = []

        # calculate damage
        if buffcheck:
            buffeddamage = self.owner.check_buffs(damage, "injury")
        _hp = int(self.hp)
        taken = round(buffeddamage) if buffeddamage < _hp else _hp
        overkill = max(buffeddamage - taken, 0)
        defender_tags.append("attacked")
        if taken > 0:
            defender_tags.append("injured")

        # context updating and dict conversion (or basic values)
        if context:
            context.taken, context.overkill = taken, overkill
            context = congen([context])
        else:
            context = {
                "attacker": attacker,
                "target": self.owner,
                "damage": damage,
                "taken": taken,
                "element": element,
                "overkill": overkill,
            }

        # deal damage
        self.hp = max(self.hp - taken, 0)
        was_kill = self.hp <= 0
        if loud:
            self.owner.msg("|rYou take {0} damage!|n".format(taken))

        # assign attacker to this object's ndb
        if self.owner.ndb.attackers:
            self.owner.ndb.attackers.append(attacker)
        else:
            self.owner.ndb.attackers = [attacker]

        # death
        if was_kill:
            # if this object grants xp, and the attacker can gain it, transfer xp
            gain = self.owner.attributes.get("gain", None)
            if attacker:
                xp = attacker.attributes.has("xp")
                if gain and xp:
                    attacker.db.xp = min(gain + xp, attacker.limit)

            # die and publish death event for all attackers
            self.die(context)
            defender_tags.append("death")
            attacker_tags.append("kill")

        # fire events
        if is_event:
            if defender_tags:
                self.owner.events.publish(defender_tags, attacker, context)
            if attacker_tags:
                self.owner.events.send(attacker_tags, attacker, context)

        # return the combat context
        return CombatContext(**context)

    def die(self, context=None):
        """Die! Marks you as dead."""
        # tag and buff stuff
        self.end_combat()
        self.owner.tags.add("dead", category="combat")
        self.owner.buffs.super_remove(tag="remove_on_death")

        # messaging
        messaging = self.owner.attributes.get("messaging", {})
        message = messaging.get("death", DEFAULT_DEATH_MSG)
        formatted = capitalize(message.format(owner=self.owner))

        # send message and delay revive
        self.owner.location.msg_contents(formatted)
        utils.delay(10, _revive, self.owner, persistent=True)

    def revive(self):
        """Revive! You aren't dead anymore!"""
        _revive(self.owner)

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
        vs evasion roll, or a blast vs awareness roll. Each roll is
        d100 + random(acc/eva), and a hit is made if the hit value is higher.
        Crits require that the hit roll be greater than the evasion roll by the specified multiplier.

        Args:
            acc:    (default: 0) The attacker's accuracy modifier.
            eva:    (default: 0) The target's evasion modifier.
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
        hit, eva = StatContext(**_h), StatContext(**_d)

        update = {
            "hit": hit,
            "eva": eva,
            "div": (_hit + accuracy) / (_dodge + evasion),
            "damage": damage,
            "isHit": (_hit + accuracy) > (_dodge + evasion),
            "isCrit": _hit > _dodge * crit,
        }

        # Generate the AttackContext
        context: AttackContext = AttackContext(**update)
        return context

    # region attack types
    def basic_attack(
        self,
        stats: OffenseStats,
        target,
    ) -> AttackContext:
        """
        Performs a basic attack against the target. This is the building block of all other attacks.
        This is an opposed hit against the specified defense stat, then modified by armor and crit.

        Args:
            stats:      The offensive stats to use. OffenseStats dataclass
            target:     The defending object

        Returns an AttackContext.

        """

        evasion = getattr(target, stats.opposing, 0)
        attack = self.opposed_hit(stats.accuracy, evasion)

        # if attack was successful
        if attack.isHit:
            # if crit (hit > evasion * crit), multiply damage
            if attack.isCrit:
                precision_mult = self.buffs.check(stats.mult, "precision")
                attack.damage *= precision_mult

            # damage modification
            attack.deflected = target.combat.deflect(attack.damage)

        return attack

    def aoe(
        self,
        stats: OffenseStats,
        targets: list,
        exclude: list = None,
        hurt=False,
    ):
        """Performs an AoE attack, which attempts to hit all specified targets once.

        Args:
            stats:      The offensive stats to use. OffenseStats dataclass
            targets:    The list of targets
            exclude:    The list of objects to exclude from the target pool (default: None)
            hurt:       If this AoE hurts the attacker too (default: False)

        """
        if not targets:
            return
        attacks = []

        # find targets via set comparison
        _t = set(targets)
        _e = set(exclude)
        if not hurt:
            _e.add(self.owner)
        valids = _t.difference(_e)

        # attempt a basic attack on each target
        for target in valids:
            attack = self.basic_attack(stats, target)

    def rapid(
        self,
        stats: OffenseStats,
        defender,
        shots: int = 1,
        burst=False,
    ):
        """
        Performs a rapid attack, which attempts to attack a single target multiple times until it misses.

        Args:
            stats:      The offensive stats to use. OffenseStats dataclass
            defender:   The defending object
            shots:      How many attacks to make (default: 1)
            burst:      If this attack continues even if a miss occurs (default: False)

        """
        messaging = ""

        attacker = self.owner
        total = 0

        # for each shot
        for x in range(shots):
            # perform a basic attack
            attack: AttackContext = self.basic_attack(stats, defender, "awareness")
            damagelist = ""

            # if this is the first shot, create the initial messaging
            if x == 0:
                hitmapping = {"hit": attack.hit.total, "eva": attack.eva.total}
                rollmsg = "  HIT: +{hit} vs EVA: +{eva}".format(**hitmapping)
                messaging += rollmsg + NEWLINE

            # if we miss
            if not attack.isHit:
                damagelist += " Miss!"
                # only burst weapons continue firing after a miss
                if not burst:
                    break

            # if we hit
            if attack.isHit:
                m = " {0} damage!".format(attack.deflected)
                if attack.isCrit:
                    m = "|520" + m + "|n"
                damagelist += m
                total += attack.deflected

            messaging += INDENT + PREFIX + damagelist + NEWLINE

        # apply total damage buffs
        total = _enhance_total(total, attacker)

        messaging += (INDENT + "  = {0} total damage!").format(*total) + NEWLINE
        attacker.location.msg_contents(messaging)

    def weapon_attack(self, weapon: WeaponStats, target: Object):
        """
        Performs an attack against a target, according to the weapon's various stats

        Args:
            weapon:   The weapon you are using. WeaponStats dataclass
            target:   The target you are attacking
        """
        # initial context
        attacker: Object = self.owner
        weapon_object = attacker.attributes.get("held", None)
        _basics = {
            "attacker": attacker,
            "target": target,
            "weapon": weapon,
            "attacks": [],
            "element": "neutral",
        }
        combat: CombatContext = CombatContext(**_basics)

        # variable assignments
        accuracy_modified = attacker.buffs.check(weapon.accuracy, "accuracy")
        evasion = getattr(target, "evasion", 0)

        # opening damage message formatting
        mapping = congen([combat])
        mapping.update(
            {
                "weapon": weapon.weapon,
                "attacker": attacker.get_display_name(),
                "target": target.get_display_name(),
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
                hitmapping = {"hit": attack.hit.total, "eva": attack.eva.total}
                roll_msg = "  HIT: +{hit} vs EVA: +{eva}"
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
                attacker.events.publish(["hit"], attacker, context)

                # damage modification
                attack.deflected = target.combat.deflect(attack.damage)
                combat.attacks.append(attack)

        # hit (at least one successful hit)
        if was_hit:
            # damage messaging setup
            message = " {0} damage!"
            dmglist_msg = ""

            # individual attack messages and damage totaling
            for atk in combat.attacks:
                dmg = round(atk.deflected)
                if dmg <= 0:
                    dmg = "No"
                if atk.isCrit:
                    dmg = "|520" + str(dmg)
                dmglist_msg += message.format(dmg) + "|n"
                combat.damage += atk.damage
                combat.taken += atk.deflected

            # attacks message
            attacker.location.msg_contents(INDENT + PREFIX + dmglist_msg)

            # apply total damage buffs
            if weapon_object:
                combat.damage = weapon_object.buffs.check(combat.damage, "total_damage")
            combat.damage = attacker.check_buffs(combat.damage, "total_damage")

            # total damage message
            TOTAL = "  = "
            message = "{0} total damage!".format(round(combat.taken))
            if combat.damage:
                attacker.location.msg_contents(INDENT + TOTAL + message)

            # hit messaging
            formatted, msg = "", ""

            mapping = congen([combat])

            if not combat.taken:
                msg = DEFAULT_TEMP_MSG["bullet"]["invuln"]
            elif was_crit:
                msg = weapon.messaging.get("crit", DEFAULT_CRIT_MSG)
            else:
                msg = weapon.messaging.get("hit", DEFAULT_HIT_MSG)

            formatted = msg.format(**mapping)
            capitalized = capitalize(formatted)
            attacker.location.msg_contents("|520" + INDENT + capitalized)

            # injury
            target.combat.injure(combat.damage, attacker, context=combat)

        # miss
        else:
            attacker.location.msg_contents(INDENT + PREFIX + " Miss!")
            attacker.events.publish(["miss"], weapon_object, combat)

        return combat

    # endregion


def _revive(target):
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


def rainbowfy(string: str):
    colortable = ["|r", "|520", "|y", "|g", "|b", "|i", "|b", "|g", "|y", "|520", "|r"]
    split: list = string.split()
    rainbow = [colortable[i % 12] + stri for i, stri in enumerate(split)]
    joined = "".join(rainbow)
    return joined


def _enhance_total(value, attacker):
    """Enhances total damage via buffs for weapon (if applicable) and character"""
    weapon_object = attacker.attributes.get("held", None)
    if weapon_object:
        total = weapon_object.buffs.check(value, "total_damage")
    total = attacker.check_buffs(value, "total_damage")
    return total
