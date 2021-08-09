from typeclasses.context import Context, BuffContext, generate_context
from typeclasses.perk import Perk
import typeclasses.handlers.buffhandler as bh

class RampagePerk(Perk):
    trigger = 'hit'
    slot = 'style1'

    stack_msg = {
        1: 'You feel a bloodlust welling up inside you.',
        2: 'Your bloodlust calls to you.',
        3: 'All must die.'
    } 

    def on_trigger(self, context: Context):
        bc: BuffContext = bh.add_buff(context.actor, context.actee, 'rampage')

        msg = ''
        if bc.stacks in self.stack_msg: context.actee.msg( self.stack_msg[bc.stacks] )
        return bc

class ExploitPerk(Perk):

    trigger = 'hit'
    slot = 'style1'

    stack_msg = {
        1:"You begin to notice flaws in your opponent's defense.",
        10:"You're certain you've found a weakness. You just need more time.",
        20:"A perfect opportunity presents itself."
    }

    trigger_msg = ''

    def on_trigger(self, context: Context) -> BuffContext:
        if 'exploited' in context.actor.db.effects: return generate_context(context=context, msg='')
        bc: BuffContext = bh.add_buff(context.actor, context.actee, 'exploit')
        if bc.stacks in self.stack_msg: context.actee.msg( self.stack_msg[bc.stacks] )
        return bc

class PerkList():
    rampage = RampagePerk
    exploit = ExploitPerk