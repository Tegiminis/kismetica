from evennia import lockfuncs
from evennia import Command as BaseCommand
from world import destiny_rules
from typeclasses import characters as Character
from evennia import utils
import time

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
        caller = self.caller    
        target = None
        now = time.time()
        slot = caller.db.equipped_held

        if caller.db.cooldowns['basic'] is not None:
            cd = caller.db.cooldowns['basic']
            rpm = caller.db.equipped_weapons[slot].db.speed['fire']

        if cd and now - cd < rpm:
            caller.msg("You cannot fire again so quickly!")
            return

        if self.args:
            target = caller.search(self.args)
            caller.ndb.target = target
        elif caller.ndb.target:
            target = caller.ndb.target
        else:
            caller.msg("You need to pick a target to attack.")
            return

        msg_target = target.key
        if target.db.named is False:
            msg_target = "the " + msg_target

        slot = caller.db.equipped_held
        _wep = caller.db.equipped_weapons[slot]

        shield_broke = False

        msg_post = ""

        _name = target.key
        if target.db.named is False:
            _name = "The " + _name

        if target:
            if utils.inherits_from(target, 'typeclasses.npc.NPC') or target.db.crucible == True:
                # The string of "hits" used for messaging. Looks like this once everything's done: "15! 10! Miss! 10! 10!"
                str_hits = ""
                shots = _wep.db.damage['shots'] 
                total = 0
                for x in range(shots):
                    _hit = destiny_rules.roll_hit(caller, target)
                    _dmg = destiny_rules.combat_damage(caller, target, *_hit)
                    _prv = target.db.shield['current']

                    if _dmg <= 0:
                        str_hits += "|nMiss! "
                    else:
                        destiny_rules.damage_target(_dmg, target)
                        total += _dmg
                        if _hit[1] is True:
                            str_hits += "|y%i! " % _dmg
                        else:
                            str_hits += "|n%i! " % _dmg

                        if target.db.shield['current'] < _prv and target.db.shield['current'] == 0 and shield_broke == False:
                            msg_post += "%s's shield cracks and shatters!" % _name
                            shield_broke = True

                        if target.db.health['current'] <= 0:
                            str_hits += "|rKill shot!|n"
                            msg_post += "\n|n" + target.db.msg_death
                            utils.delay(3.0, destiny_rules.revive, target)
                            break

                
                # Messaging
                caller.msg(
                    ( "\n|n" + _wep.db.msg['attack'] % msg_target ) +
                    ( "\n|n" + str_hits ) +
                    ( "\n|n" + " = %s damage!" % str(total) ) +
                    ( "\n|n" + msg_post)
                    )

                if utils.inherits_from(caller, 'typeclasses.characters.PlayerCharacter'):
                    caller.db.cooldowns['basic'] = now

                utils.delay(rpm, caller.msg, _wep.db.msg['cooldown'])

            else:
                caller.msg("You must select a valid target to attack!")
                return

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
        name = target.name

        if target:
            if target.location.id == caller.id:
                caller.db.equipped_weapons[target.db.slot] = target
                caller.msg("You hoist the %s in your hands. %s" % (name, target.db.msg['equip']))

                if caller.db.named:
                    caller.location.msg_contents("%s hoists the %s in their hands." % (caller.name, name), exclude=caller)
                else:
                    caller.location.msg_contents("The %s hoists the %s in their hands." % (caller.name, name), exclude=caller)
                return
            else:
                caller.msg("You must have a weapon in your inventory in order to equip it.")
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

        caller.db.equipped_held = self.args

class CmdPTest(BaseCommand):
    """
    Tests if locks can use dicts

    Usage:
      ptest

    A debug command to test lockfuncs.
    """

    key = "ptest"
    locks = "cmd: perm(Builder)"
    help_category = "General"

    def parse(self):
        self.target = self.args.strip()

    def func(self):
        caller = self.caller
        _str = lockfuncs.attr(self.caller, self.caller, "locktest", "8", compare="gt")
        caller.msg("Attr() returned: %s" % _str)