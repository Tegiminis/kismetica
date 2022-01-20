from typeclasses.content.workshop import RapidHit
from typeclasses.content.perklist import ExploitPerk, LeechRoundPerk, RampagePerk, ThornsPerk, WeakenPerk
from typeclasses.context import Context
from evennia import lockfuncs
from evennia import Command as BaseCommand
from world import rules
from typeclasses import characters as Character
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
            buff: Context = target.buffs.add(self.args[1])
            pass

class CmdPerk(BaseCommand):
    """
    Add perk to a target.

    Usage:
      perk <target> <perk> <slot>

    Applies the specified perk to the target. If slot is included, will use that instead of the perk id for the dictionary key. 
    """
    key = "perk"
    aliases = ["perk"]

    perklist = {
        'rampage' : RampagePerk,
        'exploit' : ExploitPerk,
        'weaken' : WeakenPerk,
        'leech' : LeechRoundPerk,
        'thorns' : ThornsPerk
    }
    
    def parse(self):
        self.args = self.args.split()

    def func(self):
        caller = self.caller    
        target = None
        now = time.time()
        slot = None

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

        if length == 3: slot = self.args[2]

        _perk = self.perklist.get(self.args[1])
        caller.msg('Debug: Perk applied = ' + str(_perk))

        if target and _perk: target.perks.add(_perk, slot)
        else: caller.msg("Invalid perk.")