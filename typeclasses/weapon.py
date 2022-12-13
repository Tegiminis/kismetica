import random
import time
import inflect
from typing import TYPE_CHECKING
from evennia.typeclasses.attributes import AttributeProperty
from evennia.typeclasses.tags import TagHandler

from typeclasses.components.cooldowns import CooldownHandler
from typeclasses.objects import Object
from evennia.contrib.rpg.buffs.buff import BaseBuff, BuffableProperty
from typeclasses.components.buffsextended import BuffHandlerExtended
from evennia.utils import lazy_property, utils
from evennia import Command as BaseCommand
from evennia import CmdSet
from world.rules import make_context

p = inflect.engine()

if TYPE_CHECKING:
    from typeclasses.characters import Character

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


class ClampedStat(AttributeProperty):
    def at_get(self, value, obj):
        _value = obj.buffs.check(value, self._key)
        _value = min(max(0, _value), 100)
        return _value


class FusionCharging(BaseBuff):
    key = "fusioncharging"
    unique = True
    duration = 5

    def at_remove(self, *args, **kwargs):
        player = self.owner.location
        self.owner.buffs.add(FusionCharged)
        pass


class FusionCharged(BaseBuff):
    key = "fusioncharged"

    duration = 30
    unique = True
    tickrate = 5

    tick_msg = {
        1: "Your %s vibrates in your hands, ready to unleash.",
        3: "The barrel of your %s begins to glow, and the vibrating grows stronger.",
        5: "You hear a low whine as heat radiates from the chamber of your %s, scalding your hands.",
    }

    def at_expire(self, *args, **kwargs):
        player: Character = self.owner.location
        _dmg = round(player.maxhp * 0.75)
        player.msg(
            "\n|nYour {weapon} explodes, filling your lungs with searing plasma!".format(
                weapon=self.owner
            )
        )
        player.combat.take_damage(_dmg)

    def at_tick(self, *args, **kwargs):
        _tn = self.ticknum
        if _tn in self.tick_msg.keys():
            self.owner.location.msg(self.tick_msg[_tn] % self.owner)


class CmdReload(BaseCommand):
    """
    Reloads this weapon if it is in the equipped slot.

    Usage:
      rel

    """

    key = "rel"
    locks = ""

    def parse(self):
        pass

    def func(self):
        _caller = self.caller
        _obj = self.obj
        mapping = {"character": _caller, "weapon": self.obj}
        self.obj.reload_weapon()
        _caller.msg("You slap a new mag into your {weapon}.".format(**mapping))
        _caller.location.msg_contents(
            "{character} reloads their {weapon}.".format(**mapping), exclude=_caller
        )
        return


class CmdShoot(BaseCommand):
    """
    Shoots this weapon.

    Usage:
      shoot

    """

    key = "shoot"
    locks = ""

    def parse(self):
        self.args = self.args.strip()

    def func(self):
        caller = self.caller
        target = None

        if self.args:
            target = caller.search(self.args)
            caller.ndb.target = target
        elif caller.ndb.target:
            target = caller.ndb.target
        else:
            caller.msg("You need to pick a target to attack.")
            return

        if target.db.state == "dead":
            caller.msg("You cannot attack a dead target.")
            return

        if caller.cooldowns.find("attack"):
            caller.msg("You cannot act again so quickly!")
            return

        if target:
            self.obj.attack(target)
        else:
            caller.msg("You must select a valid target to attack!")
            return


class CmdCharge(BaseCommand):
    """
    Charges this weapon. Used on fusion rifles only

    Usage:
      charge

    """

    key = "charge"
    locks = ""

    def parse(self):
        pass

    def func(self):
        _caller = self.caller
        _obj: Object = self.obj
        tags: TagHandler = _obj.tags

        # flavor on bullet weapons
        if not _obj.tags.has("fusion", "weapon"):
            _caller.msg(
                "You rack the {weapon}'s charging handle fruitlessly.".format(
                    weapon=_obj
                )
            )
            return

        # start charging
        _obj.buffs.add(FusionCharging)

        # messaging
        _caller.msg("You begin to charge your %s." % _obj)
        _caller.location.msg_contents(
            "%s charges their %s." % (_caller, _obj), exclude=_caller
        )
        return


class WeaponCmdSet(CmdSet):

    key = "WeaponCmds"

    def at_cmdset_creation(self):
        self.add(CmdReload())
        self.add(CmdCharge())
        self.add(CmdShoot())


class Weapon(Object):
    """
    A weapon that can be used by player characters.
    """

    @lazy_property
    def buffs(self) -> BuffHandlerExtended:
        return BuffHandlerExtended(self)

    @lazy_property
    def perks(self) -> BuffHandlerExtended:
        return BuffHandlerExtended(self, dbkey="perks")

    # ammo
    mag = BuffableProperty(10)
    inventory = BuffableProperty(0)

    # neutral stats (clamped)
    accuracy = ClampedStat(50)
    stability = ClampedStat(10)
    range = ClampedStat(10)

    # damage stats
    damage = BuffableProperty(10)
    penetration = BuffableProperty(1)
    spread = BuffableProperty(1.0)
    combo = BuffableProperty(1.0)

    # cooldowns
    equip = BuffableProperty(20)
    reload = BuffableProperty(15)
    rpm = BuffableProperty(5)

    # crits
    crit = BuffableProperty(2)
    precision = BuffableProperty(2)

    def at_object_creation(self):
        "Called when object is first created"

        self.cmdset.add(WeaponCmdSet, permanent=True)
        self.locks.add("call:equipped()")
        self.tags.add(key="primary", category="ammo")
        self.tags.add(key="fusion", category="weapon")

        # Ammo stats
        self.db.ammo = 5  # Amount of shots you can make
        self.mag  # Mag size; what you reload to
        self.db.reserves = 0  # Amount of ammo you have in reserve
        self.inventory  # Amount of ammo you can hold in reserve

        # Damage stats
        self.damage  # Base damage
        self.stability  # Increases low damage bracket
        self.range  # Increases upper damage bracket
        self.penetration  # Flat armor penetration value

        # Hit/shot stats
        self.accuracy  # Percent of weapon proficiency used for accuracy
        self.spread  # Chance to attack multiple targets
        self.combo  # Chance to attack the first target multiple times

        # Speed stats for doing particular actions (forces cooldown)
        self.equip
        self.reload
        self.rpm

        # Crit chance and multiplier
        self.crit
        self.precision

        # Messages for your weapon.
        # Most weapons only have self (what you see when you attack) and attack (what the room sees when you attack)
        # Exotics and altered weapons might have unique messages
        self.db.msg = {
            "self": "You shoot your {weapon} at {defender}.",
            "attack": "{attacker} shoots their {weapon} at {defender}.",
        }

        # Gun's rarity. Common, Uncommon, Rare, Legendary, Unique, Exotic. Dictates number of perks when gun is rolled on.
        self.db.rarity = 1

    @property
    def magcheck(self):
        """Gives you an adjective string determined by the magazine fill percentage."""

        _str = ""
        _perc = self.db.ammo / self.db.mag

        if _perc > 1.0:
            _str = "overflowing"
        elif _perc == 1.0:
            _str = "topped off"
        elif _perc > 0.8:
            _str = "nearly full"
        elif _perc > 0.6:
            _str = "lightly used"
        elif _perc > 0.4:
            _str = "roughly half"
        elif _perc > 0.2:
            _str = "running low"
        elif _perc > 0:
            _str = "almost out"
        elif _perc <= 0:
            _str = "concerningly empty"

        return _str

    # region properties

    @property
    def randomized_damage(self):
        """Returns a randomized damage value."""
        _dmg = self.damage
        _min = int(_dmg * 0.5 + (0.5 * (self.stability / 100)))
        _max = int(_dmg * 1.5 + (0.5 * (self.range / 100)))
        _ret = random.randint(_min, _max)
        return _ret

    @property
    def shots(self):
        """Returns the number of shots this weapon will fire. Based on combo stat."""
        _combo = self.combo
        _shots = (
            round(random.random() * _combo)
            if not self.tags.has("burst", category="weapon")
            else int(self.combo)
        )
        return _shots

    @property
    def ammo(self):
        """This weapon's current ammo."""
        return self.db.ammo

    @ammo.setter
    def ammo(self, amount):
        self.db.ammo = amount

    @property
    def skilled_accuracy(self):
        """Returns the "skill accuracy" of the weapon, equal to the character's
        weapon skill multiplied by the accuracy bonus."""

        return 100 * min(self.accuracy / 100, 1)

    def at_init(self):
        owner: Object = self.location
        _b, _p = self.buffs, self.perks
        if owner.attributes.has("held"):
            if owner.db.held == self:
                owner.events.subscribe(self.buffs)
                owner.events.subscribe(self.perks)

        return super().at_init()

    # endregion

    # region methods
    def attack(self, defender, context=None):
        """
        Performs an attack against a defender, according to the weapon's various stats

        Args:
            defender:   The target you are attacking
            context:    (optional) The context you want to feed into the attack method
        """
        # initial context
        combat = make_context(context)
        defender: Character = defender
        attacker: Character = self.location
        _basics = {
            "attacker": attacker,
            "defender": defender,
            "weapon": self,
            "damage_instances": [],
        }
        combat.update(_basics)

        # variable assignments
        _acc = attacker.buffs.check(self.accuracy, "accuracy")
        _eva = defender.evasion

        # variable assignment
        _crit = self.crit
        base_msg = self.db.msg["self"].format(**combat)
        room_msg = self.db.msg["attack"].format(**combat)

        attacker.msg(base_msg)
        attacker.location.msg_contents(room_msg, exclude=attacker)
        _shots = self.shots
        was_hit = False
        was_crit = False
        total_damage = 0
        dmg_instances = []

        for x in range(max(1, _shots)):
            # roll to hit and update variables
            combat = attacker.combat.opposed_hit(_acc, _eva, _crit, combat)
            _is_hit = combat.get("is_hit", False)

            _hit = combat.get("hit").get("total")
            _dodge = combat.get("dodge").get("total")

            if x == 0:
                roll_msg = "  HIT: +{hit} vs EVA: +{dodge}"
                attacker.msg(roll_msg.format(hit=_hit, dodge=_dodge))

            if _is_hit:
                # precision check
                was_hit = True
                combat.update({"damage": self.randomized_damage})
                _is_crit = combat.get("is_crit", False)

                # crit multiply
                if _is_crit:
                    was_crit = True
                    _damage = combat.get("damage", 0)
                    _prec = attacker.buffs.check(self.precision, "precision")
                    _critdmg = _damage * _prec
                    combat.update({"damage": _critdmg})

                attacker.events.receive(self, "hit", combat)

                # damage application
                _damage = combat.get("damage", 0)
                combat = defender.combat.calc_damage(attacker, _damage, context=combat)

            else:
                if x == 0:
                    attacker.location.msg_contents("    ... Miss!")
                    attacker.events.receive(self, "miss", combat)
                break

        # outro messaging
        if was_hit:

            # damage messaging
            for x in combat["damage_instances"]:
                dmg_msg = "    ... {dmg} damage!"
                dmg_ = x
                if dmg_ == 0:
                    dmg_msg = "    ... no damage!"
                attacker.location.msg_contents(dmg_msg.format(dmg=dmg_))
                total_damage += dmg_

            # apply total damage buffs
            total_damage = self.buffs.check(total_damage, "total_damage")

            # total damage message
            if total_damage:
                total_msg = "      = {dmg} total damage!"
                attacker.location.msg_contents(total_msg.format(dmg=total_damage))

            # hit messaging
            hit_msg = DEFAULT_ATTACK_MSG["bullet"]["hit"]
            crit_msg = DEFAULT_ATTACK_MSG["bullet"]["crit"]
            invuln_msg = DEFAULT_ATTACK_MSG["bullet"]["invuln"]
            _msgH = hit_msg.format(**combat).capitalize()
            _msgC = crit_msg.format(**combat).capitalize()
            _msgI = invuln_msg.format(**combat).capitalize()

            if not total_damage:
                attacker.location.msg_contents("    " + _msgI)
            elif was_crit:
                attacker.location.msg_contents("    " + _msgC)
            else:
                attacker.location.msg_contents("    " + _msgH)

            combat = defender.combat.take_damage(
                total_damage, source=attacker, context=combat
            )

        attacker.location.msg_contents("|n\n")

    def reload_weapon(self) -> int:
        """Reloads this weapon and returns the amount of ammo that was reloaded."""
        _return = 0

        # Get the weapon's ammo, mag (max ammo), and figure out how much you are reloading
        _ammo = self.ammo
        _mag = self.mag
        _toreload = _mag - _ammo

        # Primary weapons don't use reserves, so if this is a primary ammo weapon, skip all the reserves stuff!
        if ("primary", "ammo") in self.tags.all(True):
            _return = _toreload
            self.db.ammo = _mag
            return _return

        # Find and check reserve count
        _reserves = self.db.reserves
        if _reserves <= 0:
            return 0

        # If you have to reload more than you have in reserves, then only reload what you can. Otherwise, top off.
        if _toreload > _reserves:
            _return = _reserves
            self.db.ammo += _reserves
            self.db.reserves = 0
        else:
            _return = _toreload
            self.db.ammo += _toreload
            self.db.reserves -= _toreload

        return _return

    def _unequip(self):
        owner = self.location
        owner.events.unsubscribe(self.buffs)

    def _equip(self):
        owner = self.location
        owner.events.subscribe(self.buffs)

    # endregion
