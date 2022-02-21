import random
from typeclasses.buff import Buff, Perk, Mod
from typeclasses.context import Context
    
class RampageBuff(Buff):
    key = 'rampage'
    name = 'Rampage'
    flavor = 'Defeating an enemy has filled you with bloodlust.'

    duration = 30

    refresh = True
    stacking = True
    unique = True
    maxstacks = 3

    mods = [ Mod('damage', 'mult', 0.15, 0.15) ]

    def on_expire(self, context: Context):
        context.origin.location.msg('The bloodlust fades.')

class Exploit(Buff):
    key = 'exploit'
    name = 'Exploit'
    flavor = "You are learning your opponent's weaknesses."

    trigger = 'hit'

    duration = 30

    refresh = True
    stacking = True
    unique = True
    maxstacks = 20

    def on_trigger(self, context: Context) -> Context:
        chance = context.buffStacks / 20
        roll = random.random()

        if chance > roll:
            context.origin.buffs.add(Exploited)
            context.origin.location.msg("An opportunity presents itself!")
            context.origin.buffs.remove('exploit')
        
        return context

    def on_expire(self, context: Context) -> str:
        context.origin.location.msg("The opportunity passes.")

class Exploited(Buff):
    key = 'exploited'
    name = 'Exploited'
    flavor = "You have sensed your target's vulnerability, and are poised to strike."

    duration = 30

    refresh = True
    stacking = False
    unique = True

    mods = [ Mod('damage', 'add', 100) ]

    def after_check(self, context: Context):
        context.origin.msg( "You exploit your target's weakness!" )
        context.origin.buffs.remove('exploited', delay=0.01)

    def on_remove(self, context: Context):
        context.origin.msg( "\n|nYou cannot sense your target's weakness anymore." )

class Weakened(Buff):
    key = 'weakened'
    name = 'Weakened'
    flavor = 'An unexplained weakness courses through this person.'

    duration = 30

    refresh = True
    stacking = False
    unique = True

    mods = [ Mod('injury', 'add', 100) ]

class Leeching(Buff):
    key = 'leeching'
    name = 'Leeching'
    flavor = 'Attacking this target fills you with vigor.'

    duration = 30

    refresh = True
    stacking = False
    unique = True

    trigger = 'thorns'

    def on_trigger(self, context: Context) -> Context:
        target = context.target
        target.msg('Debug: Attempting leech.')
        heal = context.damage * 0.1
        target.heal(heal)

class Poison(Buff):
    key = 'poison'
    name = 'Poison'
    flavor = 'A poison wracks this body.'

    duration = 30

    refresh = True
    stacking = True
    maxstacks = 5
    unique = True

    ticking = True
    tickrate = 5

    dmg = 5

    def on_tick(self, context: Context) -> Context:
        _dmg = self.dmg * context.buffStacks
        context.target.location.msg_contents("Poison courses through %s's body, dealing %i damage." % (context.target.named,_dmg))
        context.target.damage_health(_dmg)

class BuffList():
    '''Initialization of buff and effect typeclasses used to apply buffs to players.

    If it's not in this list, it won't be applicable in-game without python access.'''
    # Buffs
    rampage = RampageBuff
    exploited = Exploited
    exploit = Exploit
    leeching = Leeching
    poison = Poison