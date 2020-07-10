from evennia import CmdSet
from commands import destiny_commands as basic
from commands import destiny_commands_builder as builder

class DestinyBasicCmdSet(CmdSet):
        
    key = "DestinyBasicCmdSet"

    def at_cmdset_creation(self):     
        self.add(basic.CmdAttack())
        self.add(basic.CmdTarget())
        self.add(basic.CmdEquip())
        self.add(basic.CmdSwitch())
        self.add(basic.CmdPTest())

class DestinyBuilderCmdSet(CmdSet):
        
    key = "DestinyBuilderCmdSet"

    def at_cmdset_creation(self):     
        self.add(builder.CmdAlter())