import random
from typeclasses.buff import Buff, Perk, Mod
from typeclasses.context import BuffContext, generate_context
import typeclasses.handlers.buffhandler as bh
    
class RampageBuff(Buff):
    id = 'rampage'
    name = 'Rampage'
    flavor = 'Defeating an enemy has filled you with bloodlust.'

    duration = 30

    refresh = True
    stacking = True
    unique = False
    maxstacks = 3

    mods = [ Mod('damage', 'mult', 0.15, 0.15) ]

    def on_expire(self, context: BuffContext):
        context.owner.msg('The bloodlust fades.')

class Exploit(Buff):
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
            bh.add_buff(context.origin, context.origin, Exploited)
            context.owner.msg("An opportunity presents itself!")
            bh.remove_buff(context.origin, context.origin, 'exploit')
        
        return context

    def on_expire(self, context: BuffContext) -> str:
        context.owner.msg("The opportunity passes.")

class Exploited(Buff):
    id = 'exploited'
    name = 'Exploited'
    flavor = "You have sensed your target's vulnerability, and are poised to strike."

    duration = 30

    refresh = True
    stacking = False
    unique = False

    mods = [ Mod('damage', 'add', 100) ]

    def after_check(self, context: BuffContext):
        context.owner.msg( "You exploit your target's weakness!" )
        bh.remove_buff(context.origin, context.origin, 'exploited', delay=0.01)

    def on_remove(self, context: BuffContext):
        context.owner.msg( "\n|nYou cannot sense your target's weakness anymore." )

class Weakened(Buff):
    id = 'weakened'
    name = 'Weakened'
    flavor = 'An unexplained weakness courses through this person.'

    duration = 30

    refresh = True
    stacking = False
    unique = False

    mods = [ Mod('injury', 'add', 100) ]

class Leeching(Buff):
    id = 'leeching'
    name = 'Leeching'
    flavor = 'Attacking this target fills you with vigor.'

    duration = 30

    refresh = True
    stacking = False
    unique = False

    trigger = 'thorns'

    def on_trigger(self, context: BuffContext) -> BuffContext:
        target = context.target
        target.msg('Debug: Attempting leech.')
        heal = context.dc.damage * 0.1
        target.add_health(heal)

class BuffList():
    '''Initialization of buff and effect typeclasses used to apply buffs to players.

    If it's not in this list, it won't be applicable in-game without python access.'''
    # Buffs
    rampage = RampageBuff
    exploited = Exploited
    exploit = Exploit
    leeching = Leeching