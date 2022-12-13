from world import loot
import evennia.prototypes.spawner as spawner
from evennia import CmdSet, Command as BaseCommand
from typeclasses.item import Item


class EngramCmdSet(CmdSet):

    key = "EngramCmdSet"

    def at_cmdset_creation(self):
        self.add(CmdDecrypt())
        self.add(CmdGuess())


class CmdDecrypt(BaseCommand):
    """
    Decrypt this engram.

    Usage:
      decrypt

    """

    key = "decrypt"
    locks = ""

    def parse(self):
        pass

    def func(self):
        caller = self.caller
        engram: Engram = self.obj
        result = engram.decrypt()
        caller.msg("You successfully decrypt the engram into a " + result + "!")
        return


class CmdGuess(BaseCommand):
    """
    Guess the contents of this engram.

    Usage:
      guess <item>

    """

    key = "guess"
    locks = ""

    def parse(self):
        self.args = self.args.strip()

    def func(self):
        caller = self.caller
        engram: Engram = self.obj
        drop = dict(engram.db.drop)
        correct_answer = drop["key"]

        if not engram.tags.has("guessed") and self.args:
            caller.msg("You guessed: " + self.args)
            if self.args == correct_answer:
                caller.msg("... You have a good hunch about this!")
            else:
                caller.msg("... You feel ambivalent.")

        return


class Engram(Item):
    def at_object_creation(self):
        self.cmdset.add(EngramCmdSet, permanent=True)
        pass

    def decrypt(self):
        drop = self.db.drop
        spawner.spawn(drop)
        return drop["key"]

    def guess(self):
        pass
