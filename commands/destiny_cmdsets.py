from evennia import CmdSet
import commands.destiny_commands as basic
import commands.destiny_commands_builder as builder

class DestinyBasicCmdSet(CmdSet):
        
    key = "DestinyBasicCmdSet"

    def at_cmdset_creation(self):     
        self.add(basic.CmdAttack())
        self.add(basic.CmdDisengage())
        self.add(basic.CmdMag())
        self.add(basic.CmdTarget())
        self.add(basic.CmdEquip())
        self.add(basic.CmdDraw())
        self.add(basic.CmdPTest())
        self.add(basic.CmdLootTest())
        self.add(basic.CmdCheck())

class DestinyBuilderCmdSet(CmdSet):
        
    key = "DestinyBuilderCmdSet"

    def at_cmdset_creation(self):     
        self.add(builder.CmdAlter())
        self.add(builder.CmdBuff())
        self.add(builder.CmdPerk())