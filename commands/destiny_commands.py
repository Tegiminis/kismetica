from evennia import lockfuncs
from evennia import Command as BaseCommand
import typeclasses.handlers.perkhandler as ph
from world import rules
from typeclasses import characters as Character
from evennia import utils
import typeclasses.handlers.buffhandler as bh
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
        weapon = caller.db.held

        if caller.db.cooldowns['basic'] is not None:
            cd = caller.db.cooldowns['basic']
            rpm = weapon.db.speed['fire']

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
        
        if target.db.state == 'dead':
            caller.msg("You cannot attack a dead target.")
            return

        msg_target = target.named()
        msg_caller = caller.named()

        _wep = caller.db.held

        msg_post = ''
        msg_perk = ''

        if target:
            if utils.inherits_from(target, 'typeclasses.npc.NPC') or target.db.crucible == True:
                # The string of "hits" used for messaging. Looks like this once everything's done: "15! 10! Miss! 10! 10!"
                str_hits = ''

                #Caching variables.
                shots = _wep.db.damage['shots'] 
                total = 0

                # Fires however many shots you tell it to. AKA 5 shots = 5 loops
                for x in range(shots):
                    _hit = rules.roll_hit(caller, target)                       # The hit roll
                    _dmg = rules.calculate_damage(caller, target, *_hit)     # The damage roll

                    if _hit[0]:
                            msg_perk += ph.trigger_effects(weapon, 'hit')
                            msg_perk += ph.trigger_effects(caller, 'hit')

                    if _dmg <= 0:
                        str_hits += "|nMiss! "                     # If you don't damage something, it's obviously a miss! For now.
                    else:
                        msg_perk += rules.damage_target(_dmg, target)         # Damage the target and return any effect-related messages
                        total += _dmg                                         # Add the damage you did to the total (for messaging)

                        # Formatting based on if it's a crit or not
                        if _hit[1] is True:
                            str_hits += "|y%i! " % _dmg            # Critical hit!
                        else:
                            str_hits += "|n%i! " % _dmg            # Normal hit!

                        # Killshot detection. Immediately stops the attack and breaks the for loop when target dies.
                        if target.db.health['current'] <= 0:
                            str_hits += "|rKill shot!|n"
                            msg_post += "\n|n" + (_wep.db.msg['kill'] % msg_target).capitalize()

                            break

                
                # Messaging to the shooter, target, and room, respectively.
                caller.msg(
                    ( "\n|n" + (_wep.db.msg['attack'] % ('you',msg_target)).capitalize() ) +      # The base attack string
                    ( "\n|n" + str_hits ) +                                # The hits (10! 15! Miss!)
                    ( "\n|n" + " = %s damage!" % str(total) ) +            # Total damage dealt
                    ( "\n|n" + msg_post) +                                 # Any "post" messages, such as status changes (like death)
                    ( "\n|n" + msg_perk)                                   # Any "perk" messages
                    )
                
                target.msg(
                    ( "\n|n" + (_wep.db.msg['attack'] % (msg_caller,'you')).capitalize() ) +
                    ( "\n|n" + str_hits ) +
                    ( "\n|n" + " = %s damage!" % str(total) )
                    )

                caller.location.msg_contents(
                    ( "\n|n" + (_wep.db.msg['attack'] % (msg_caller, msg_target)).capitalize() ) +
                    ( "\n|n" + str_hits ) +
                    ( "\n|n" + " = %s damage!" % str(total) ), 
                    exclude=(caller, target)
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
        name = ""
        _name = ""

        if target:
            if target.location.id == caller.id:
                caller.db.held = target
                caller.msg("You equip the %s. %s" % (name, target.db.msg['equip']))

                _name = caller.named()
                name = target.named()
                caller.location.msg_contents("%s hoists %s in their hands." % (_name, name), exclude=caller)
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
            buffs = bh.view_buffs(caller)
            if buffs:
                msg = 'You are currently buffed by: \n|n\n|n'
                for x in buffs:
                    msg += x + "\n|n"
                caller.msg(msg)
            return
        
        target = caller.search(self.args)
        buffs = bh.view_buffs(target)
        if buffs:
            msg = '%s is currently buffed by: \n|n\n|n' + target.named()
            for x in buffs:
                msg += x + "\n|n"
            caller.msg(msg)
        else:
            caller.msg('There are no buffs on the target.')  

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

