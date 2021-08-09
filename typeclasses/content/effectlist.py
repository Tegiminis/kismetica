from typeclasses.context import BuffContext, generate_context
import typeclasses.handlers.buffhandler as bh
import typeclasses.handlers.perkhandler as ph
from typeclasses.perk import Effect
import random
    
class Exploit(Effect):
    id = 'exploit'
    name = 'Exploit'
    flavor = "You are learning your opponent's weaknesses."

    trigger = 'hit'

    duration = 30

    refresh = True
    stacking = True
    unique = False
    maxstacks = 20

    def on_trigger(self, context: BuffContext) -> BuffContext:
        chance = context.stacks / 20
        roll = random.random()

        if chance > roll:
            bh.add_buff(context.actor, context.actee, 'exploited')
            bh.remove_buff(context.actor, context.actee, 'exploit')
        
        return context

    def on_expire(self, context: BuffContext) -> str:
        context.actor.msg("The opportunity passes.")