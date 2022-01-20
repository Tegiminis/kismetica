from evennia import DefaultCharacter, lockfuncs
from evennia import Command as BaseCommand
from world import rules
from typeclasses import characters as Character
from evennia import utils
import time
import world.loot as loot
from typeclasses.context import Context

class CmdAttack(BaseCommand):
    """
    Attack an opponent

    Usage:
      attack <target>

    This will attack a target in the same room. If you have selected a target 
    using the 'target' command, it will use that target instead. You can only
    attack as fast as your equipped weapon allows. Your chance to hit is 
    dependent on your weapon's accuracy and range, and your distance from the 
    target.    
    """
    key = "attack"
    aliases = ["shoot"]

    def parse(self):
        self.args = self.args.strip()

    def func(self):
        caller: DefaultCharacter = self.caller    
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
        
        if target.db.state == 'dead':
            caller.msg("You cannot attack a dead target.")
            return

        if caller.db.cooldown:
            cd = caller.db.cooldown
            rpm = weapon.rpm
            if now - cd < rpm:
                caller.msg("You cannot act again so quickly!")
                return

        if target:
            rules.basic_attack(caller, target)
        else:
            caller.msg("You must select a valid target to attack!")
            return

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
    Equip a weapon

    Usage:
      equip <target>

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
                caller.msg("You equip the %s. %s" % (target.named, target.db.msg['equip']))

                _name = caller.named
                name = target.named
                caller.location.msg_contents("%s hoists %s in their hands." % (caller.named, target.named), exclude=caller)
                return
            else:
                caller.msg("You must have a weapon in your inventory in order to equip it.")
                return
        else:
            caller.msg("You must pick a valid weapon to equip.")
            return
        return
    
class CmdSwitch(BaseCommand):
    """
    Switch to a slot's weapon

    Usage:
        switch <kinetic/energy/power>

    This will switch your active weapon to the weapon in the specified 
    slot. If used without arguments, will stow your weapon.
    """
    key = "switch"
    aliases = ["swi","weapon swap","wswap"]

    def parse(self):
        self.args = self.args.strip()

    def func(self):

        caller = self.caller
            
        if not self.args:
            caller.msg("You must pick a slot to equip!")
            return

        caller.db.held = self.args

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
                msg = 'You are currently buffed by: \n|n\n|n'
                for x in buffs:
                    msg += x + "\n|n"
                caller.msg(msg)
            return
        
        target = caller.search(self.args)
        buffs = target.buffs.view()
        if buffs:
            msg = target.name.capitalize() + ' is currently buffed by: \n|n\n|n'
            for x in buffs:
                msg += x + "\n|n"
            caller.msg(msg)
        else:
            caller.msg('There are no buffs on the target.')  

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
        caller.msg( str(caller.xpGain) )

class CmdLootTest(BaseCommand):
    """
    Testing command. Does whatever you tell it to.
    """

    key = "ltest"
    locks = "cmd: perm(Builder)"
    help_category = "General"

    table = [
        (loot.TestWeapon, 100)
    ]

    def parse(self):
        self.target = self.args.strip()

    def func(self):
        caller = self.caller
        context = Context(caller, caller)
        _t = loot.roll(1.0)
        caller.msg("Debug: Loot roll: " + str(_t) )

        if loot.roll(1.0):
            result = loot.roll_on_table(self.table, context)
            loot.parse_result(result, context)