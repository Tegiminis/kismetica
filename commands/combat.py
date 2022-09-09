from typing import TYPE_CHECKING

from evennia import DefaultCharacter, lockfuncs
from evennia import Command as BaseCommand
from evennia.commands.default.muxcommand import MuxCommand
from world import rules
from evennia import utils
import time
import world.loot as loot
from typeclasses.context import Context

if TYPE_CHECKING:
    from typeclasses.characters import PlayerCharacter
    from typeclasses.weapon import Weapon


class CmdAttack(BaseCommand):
    """
    Attack an opponent

    Usage:
      attack <target>

    This will attack a target in the same room. If you have selected a target
    using the 'target' command, it will use that target instead. You will
    continue to attack the target until you stop via disengage.
    """

    key = "attack"
    aliases = []

    def parse(self):
        self.args = self.args.strip()

    def func(self):
        caller: PlayerCharacter = self.caller
        target = None
        now = time.time()
        weapon = caller.db.held

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
            caller.tags.add("attacking", category="combat")
            caller.combat.weapon_attack(target)
        else:
            caller.msg("You must select a valid target to attack!")
            return


class CmdMag(BaseCommand):
    """
    Checks your weapon's magazine

    Usage:
      mag

    This checks the magazine of the weapon you currently have equipped.
    """

    key = "mag"
    aliases = ["magcheck"]

    def parse(self):
        self.args = self.args.strip()

    def func(self):
        caller: PlayerCharacter = self.caller
        weapon: Weapon = caller.db.held

        caller.msg("You check your magazine and see that it is %s." % weapon.magcheck)


class CmdDisengage(BaseCommand):
    """
    Stop attacking an opponent

    Usage:
      disengage
    """

    key = "disengage"
    aliases = []

    def func(self):
        caller: PlayerCharacter = self.caller
        caller.msg("You stop attacking.")
        caller.location.msg_contents("%s stops attacking." % caller, exclude=caller)
        caller.tags.remove("attacking", category="combat")


class CmdTarget(BaseCommand):
    """
    Target an opponent

    Usage:
      target <target>

    Target an object that can be attacked in the same room. This will allow
    you to use the attack command without specifying an object. Very useful
    for multi-opponent combat. Attacking a target manually will also
    automatically make it your target.
    """

    key = "target"
    aliases = ["tar"]

    def parse(self):
        self.args = self.args.strip()

    def func(self):

        caller = self.caller
        if not self.args:
            caller.msg("You need to pick a target to focus on.")
            return
        target = caller.search(self.args)

        if target:
            caller.ndb.target = target


class CmdEquip(BaseCommand):
    """
    Equip this weapon

    Usage:
      equip

    This will equip a weapon you are carrying on you to the weapon's
    relevant slot. You can equip a kinetic, an energy, and a power
    weapon. Attempting to equip to a slot you already have equipped
    will swap the weapons. You cannot unequip a weapon after equipping
    it; you must swap to another weapon on your person.

    """

    key = "equip"

    def parse(self):
        self.args = self.args.strip()

    def func(self):
        "Implementing combat"

        caller = self.caller

        if not self.args:
            caller.msg("You must pick a weapon to equip!")
            return

        target = caller.search(self.args)
        name = ""
        _name = ""

        if target:
            if target.location.id == caller.id:
                caller.db.held = target
                caller.msg("You equip the %s." % target.named)

                _name = caller.named
                name = target.named
                caller.location.msg_contents(
                    "%s hoists %s in their hands." % (caller.named, target.named),
                    exclude=caller,
                )
                return
            else:
                caller.msg(
                    "You must have a weapon in your inventory in order to equip it."
                )
                return
        else:
            caller.msg("You must pick a valid weapon to equip.")
            return
        return


class CmdDraw(BaseCommand):
    """
    Draws the specified weapon

    Usage:
        draw <weapon>

    This will switch your active weapon to specified weapon, as long as it is equipped.
    """

    key = "draw"
    aliases = ["weapon swap", "wswap"]

    def parse(self):
        self.args = self.args.strip()

    def func(self):

        caller = self.caller

        if not self.args:
            caller.msg("You must specify a weapon to draw.")
            return

        caller.db.held = self.args


class CmdHolster(BaseCommand):
    """
    Holsters your weapon in its designated holster.

    Usage:
        holster

    This puts your weapon away. You cannot fire it or
    """

    key = "holster"
    aliases = []

    def parse(self):
        self.args = self.args.strip()

    def func(self):

        caller = self.caller
        caller.db.held = None
