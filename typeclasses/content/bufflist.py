from typeclasses.buff import Buff
from typeclasses.buff import Mod
import typeclasses.handlers.buffhandler as bh
import typeclasses.content.effectlist as el
    
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

    def on_remove(self, context):
        context.msg('The bloodlust fades.')

class Exploited(Buff):
    id = 'exploited'
    name = 'Exploited'
    flavor = "You have sensed your target's vulnerability, and are poised to strike."

    duration = 30

    refresh = True
    stacking = False
    unique = False

    mods = [ Mod('damage', 'mult', 1, 0) ]

    def after_check(self, context):
        bh.remove_buff(context, 'exploited')

    def on_remove(self, context):
        context.msg("You cannot sense your target's weakness anymore.")

class BuffList():
    '''Initialization of buff and effect typeclasses used to apply buffs to players.

    If it's not in this list, it won't be applicable in-game without python access.'''
    # Buffs
    rampage = RampageBuff
    exploited = Exploited
    
    # Effects
    exploit = el.Exploit