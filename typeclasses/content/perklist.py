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

    def on_trigger(self, context):
        bid = bh.add_buff(context, 'rampage')
        stacks = context.db.buffs[bid]['stacks']

        val = ('msg' + str(stacks))
        context.msg( vars(RampagePerk).get(val) )

class ExploitPerk(Perk):

    trigger = 'hit'
    slot = 'style1'

    stack_msg = {
        1:"You begin to notice flaws in your opponent's defense.",
        10:"You're certain you've found a weakness. You just need more time.",
        20:"A perfect target presents itself."
    }

    def on_trigger(self, context):
        bid = bh.add_buff(context, 'exploit')
        stacks = context.db.effects[bid]['stacks']
        if stacks in self.stack_msg: context.msg( self.stack_msg[stacks] )

class PerkList():
    rampage = RampagePerk
    exploit = ExploitPerk