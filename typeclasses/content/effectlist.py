import typeclasses.handlers.effecthandler as eh
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

    def on_trigger(self, context):
        handler: dict = context.db.effects
        chance = handler['exploit']['stacks'] / 20
        roll = random.random()

        if roll > chance:
            eh.add_effect(context, 'exploited')

    def on_remove(self, context):
        context.msg('The bloodlust fades.')