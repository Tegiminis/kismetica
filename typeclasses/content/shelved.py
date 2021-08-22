'''For content which is otherwise inaccessible'''

from typeclasses.context import Context, BuffContext, generate_context
from typeclasses.buff import Buff, Perk, Trait, Effect, Mod
import typeclasses.handlers.buffhandler as bh
import random

class ExploitPerk(Perk):

    id = 'exploit'
    name = 'Exploit'
    flavor = 'Shooting an enemy with this weapon allows you to find their weakness.'

    trigger = 'hit'

    stack_msg = {
        1:"You begin to notice flaws in your opponent's defense.",
        10:"You're certain you've found a weakness. You just need more time.",
        20:"You've discovered your opponent's weak spot."
    }

    trigger_msg = ''

    def on_trigger(self, context: Context) -> BuffContext:
        if 'exploited' in context.actee.db.buffs: return
        bc: BuffContext = bh.add_buff(context.actor, context.actee, 'exploit')
        if bc.stacks in self.stack_msg: context.actee.msg( self.stack_msg[bc.stacks] )
        return bc

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
            context.actor.msg("An opportunity presents itself!")
            bh.remove_buff(context.actor, context.actee, 'exploit')
        
        return context

    def on_expire(self, context: BuffContext) -> str:
        context.actor.msg("The opportunity passes.")

class Exploited(Buff):
    id = 'exploited'
    name = 'Exploited'
    flavor = "You have sensed your target's vulnerability, and are poised to strike."

    duration = 30

    refresh = True
    stacking = False
    unique = False

    mods = [ Mod('damage', 'mult', 1, 0) ]

    def after_check(self, context: BuffContext):
        context.actor.msg( "You exploit your target's weakness!" )
        bh.remove_buff(context.actor, context.actor, 'exploited', delay=0.01)

    def on_remove(self, context: BuffContext):
        context.actor.msg( "\n|nYou cannot sense your target's weakness anymore." )