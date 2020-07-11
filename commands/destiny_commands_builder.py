from evennia import lockfuncs
from evennia import Command as BaseCommand
from world import destiny_rules
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