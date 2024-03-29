from evennia import CmdSet
import commands.destiny_commands as basic
import commands.destiny_commands_builder as builder
import commands.combat as combat


class DestinyBasicCmdSet(CmdSet):

    key = "DestinyBasicCmdSet"

    def at_cmdset_creation(self):
        self.add(basic.CmdPTest())
        self.add(basic.CmdLootTest())
        self.add(basic.CmdCheck())
        self.add(combat.CmdEquip())


class DestinyBuilderCmdSet(CmdSet):

    key = "DestinyBuilderCmdSet"

    def at_cmdset_creation(self):
        self.add(builder.CmdAlter())
        self.add(builder.CmdBuff())
        self.add(builder.CmdPerk())
        self.add(builder.CmdBrainTap())
