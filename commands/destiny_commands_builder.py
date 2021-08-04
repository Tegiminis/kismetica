from evennia import lockfuncs
from evennia import Command as BaseCommand
from world import destiny_rules
from typeclasses import characters as Character
from typeclasses import buffhandler as buff
from typeclasses import perkhandler as ph
from evennia import utils
import time

class CmdAlter(BaseCommand):
    """
    Alters the messaging attributes of an object or player

    Usage:
      alter <target> <message type> <message>

    Many objects contain lists of messages which determine
    what is told to the player and to the room at large
    when actions happen.

    Alter is how you change those messages.

    You can also use "set target\msg['type'] = '<message>'"
    as that is functionally similar. The difference is this
    command won't allow you to add new messages, only
    change existing ones.    
    """
    key = "alter"
    aliases = []
    locks = "cmd: perm(Builder)"

    def parse(self):
        self.args = self.args.split()

    def func(self):
        caller = self.caller
        args = self.args

        if not self.args:
            caller.msg('Syntax: "alter <target> <message type> <message>"')
            return
        target = caller.search(args[0])

        if len(args) == 1:
            caller.msg('Error: You must pick a type of message to alter.')
            return
        msg_type = args[1]
        msg_str = ""

        if len(args) == 2:
            caller.msg('Error: You must include a message to change to.')
            return

        for x in range(2, len(args)):
            msg_str += args[x] + " "
        
        msg_str.rstrip()

        try: 
            test = target.db.msg[msg_type]
            target.db.msg[msg_type] = msg_str
            caller.msg('You successfully changed the %s message on %s to "|w%s"|n' % (msg_type, target, msg_str))
            return
        except:
            caller.msg('Error: Pick an existing message type.')
            return

        return

class CmdNPCState(BaseCommand):
    """
    Changes the NPC's state

    Usage:
      state <target> <state>

    NPCs have various "states" that they can exist in
    depending on the type of NPC. This command allows
    builders to change an NPC state on the fly.

    Functionally identical to set npc/state = <value>  
    """
    key = "npcstate"
    aliases = ["state"]
    locks = "cmd: perm(Builder)"

    def parse(self):
        self.args = self.args.split()

    def func(self):
        caller = self.caller
        args = self.args

        return

class CmdBuff(BaseCommand):
    """
    Buff a target.

    Usage:
      buff <target> <buff reference>

    Applies the specified buff to the target. All buffs are defined in bufflist.py   
    """
    key = "buff"
    aliases = ["buff"]

    def parse(self):
        self.args = self.args.split()

    def func(self):
        caller = self.caller    
        target = None
        now = time.time()

        if self.args:
            target = caller.search(self.args[0])
            caller.ndb.target = target
        elif caller.ndb.target:
            target = caller.ndb.target
        else:
            caller.msg("You need to pick a target to buff.")
            return

        if target:
            buff.add_buff(target.db.buffs, self.args[1])
            pass

class CmdPerk(BaseCommand):
    """
    Add perk to a target.

    Usage:
      perk <target> <perk reference>

    Applies the specified buff to the target. All perks are defined in perkinit.py   
    """
    key = "perk"
    aliases = ["perk"]

    def parse(self):
        self.args = self.args.split()

    def func(self):
        caller = self.caller    
        target = None
        now = time.time()

        length = len(self.args)

        if length == 2:
            target = caller.search(self.args[0])
            caller.ndb.target = target
        elif length == 1:
            caller.msg("You need to pick a perk to apply.")
            return
        else:
            caller.msg("You need to pick a target.")
            return

        if target:
            ph.add_perk(target, self.args[1])