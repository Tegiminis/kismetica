from typing import TYPE_CHECKING

from evennia import DefaultCharacter, lockfuncs
from evennia import Command as BaseCommand
from world import rules
from evennia import utils
import time
import world.loot as loot

if TYPE_CHECKING:
    from typeclasses.characters import PlayerCharacter
    from typeclasses.weapon import Weapon


class CmdCheck(BaseCommand):
    """
    Checks a target's buffs.

    Usage:
        check <target>
    """

    key = "check"
    aliases = []

    def parse(self):
        self.args = self.args.strip()

    def func(self):

        caller = self.caller

        if not self.args:
            buffs = caller.buffs.view()
            if buffs:
                msg = "You are currently buffed by: \n|n"
                for x in buffs:
                    msg += x + "\n|n"
                caller.msg(msg)
            return

        target = caller.search(self.args)
        buffs = target.buffs.view()
        msg = ""
        if buffs:
            flavorlist = list(buffs.values())
            for x in flavorlist:
                msg += ": ".join(x) + "|n\n"
            caller.msg(msg)
        else:
            caller.msg("There are no buffs on the target.")

    def view_buffs(self):
        """Formats buffs for sending to the caller"""
        pass


class CmdPTest(BaseCommand):
    """
    Testing command. Does whatever you tell it to.
    """

    key = "test"
    locks = "cmd: perm(Builder)"
    help_category = "General"

    def parse(self):
        self.target = self.args.strip()

    def func(self):
        caller = self.caller
        caller.msg(str(caller.maxhp))


class CmdLootTest(BaseCommand):
    """
    Testing command. Does whatever you tell it to.
    """

    key = "ltest"
    locks = "cmd: perm(Builder)"
    help_category = "General"

    table = [(loot.TestWeapon, 100)]

    def parse(self):
        self.target = self.args.strip()

    def func(self):
        caller = self.caller
        _t = loot.roll(1.0)
        caller.msg("Debug: Loot roll: " + str(_t))

        if loot.roll(1.0):
            result = loot.roll_on_table(self.table)
            loot.parse_result(result)
