from typeclasses.context import Context, BuffContext, generate_context
from typeclasses.buff import Buff, Perk, Trait, Effect, Mod
import typeclasses.handlers.buffhandler as bh
import typeclasses.content.bufflist as bl

class RampagePerk(Perk):
    id = 'rampage'
    name = 'Rampage'
    flavor = 'Kills with this weapon temporarily increase its damage.'

    trigger = 'kill'

    stack_msg = {
        1: 'You feel a bloodlust welling up inside you.',
        2: 'Your bloodlust calls to you.',
        3: 'All must die.'
    } 

    def on_trigger(self, context: Context):
        bc: BuffContext = bh.add_buff(context.actor, context.actee, bl.RampageBuff)
        if bc.stacks in self.stack_msg: context.actee.msg( self.stack_msg[bc.stacks] )
        return bc

class PerkList():
    rampage = RampagePerk
