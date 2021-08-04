from typeclasses.perk import BasePerk
from .buffhandler import add_buff

class Template(BasePerk):
    pass

class RampagePerk(BasePerk):
    trigger = 'hit'
    slot = 'style1'

    msg1 = 'You feel a bloodlust welling up inside you.'
    msg2 = 'Your bloodlust calls to you.'
    msg3 = 'All must die.'

    def on_trigger(self, context):
        bid = add_buff(context, 'rampage')
        stacks = context.db.buffs[bid]['stacks']

        val = ('msg' + str(stacks))
        context.msg( vars(RampagePerk).get(val) )
            