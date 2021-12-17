'''Where new perks and buffs are made!'''

from typeclasses.context import Context
from typeclasses.buff import Buff, Perk, Mod
import typeclasses.buffhandler as bh
from typeclasses.buff import Buff, Mod

class FourthTime(Perk):
    id = 'fourthtime'
    name = "Fourth Time's The Charm"
    flavor = "Rapidly landing precision hits returns two rounds to the magazine."
    
    trigger = 'crit'

    def on_trigger(self, context: Context) -> Context:
        bc: Context = bh.add_buff(context.origin, context.target, FourthTimeEffect)
        return bc

class FourthTimeEffect(Buff):
    id = 'fourthtime'
    name = "Fourth Time's The Charm"
    flavor = "Rapidly landing precision hits returns two rounds to the magazine."

    duration = 30
    maxstacks = 4

    trigger = 'crit'

    def on_trigger(self, context: Context) -> Context:
        if context.stacks >= 4: 
            context.owner.msg('Your magazine feels slightly heavier.')
            self.db.ammo += 2
            return bh.remove_buff(context.target, context.target, self.id)

class RapidHit(Perk):
    id = 'rapidhit'
    name = "Rapid Hit"
    flavor = "Precision hits temporarily increase stability and reload speed."
    
    trigger = 'crit'

    def on_trigger(self, context: Context) -> Context:
        bc: Context = bh.add_buff(context.origin, context.target, RapidHitBuff)
        return bc

class RapidHitBuff(Buff):

    id = 'rapidhit'
    name = 'Rapid Hit'
    flavor = 'Precision hits temporarily increase stability and reload speed.'

    duration = 30
    refresh = True
    stacking = True

    maxstacks = 5

    mods = [
        Mod('stability', 'add', 6, 1),
        Mod('reload', 'mult', -0.05, -0.05)
    ]

class KillClipPerk(Perk):
    id = 'killclip'
    name = 'Kill Clip'
    flavor = 'Reloading after a kill grants increased damage.'
    
    trigger = 'kill'

    def on_trigger(self, context: Context) -> Context:
        return bh.add_buff(context.origin, context.target, KillClipEffect)

class KillClipEffect(Buff):
    id = 'killclip'
    name = 'Kill Clip'
    flavor = 'Reloading after a kill grants increased damage'

    trigger = 'reload'

    duration = 30

    def on_trigger(self, context: Context) -> Context:
        context.target.msg('Your weapon begins to glow with otherworldly light.')
        return bh.add_buff(context.origin, context.target, KillClipBuff)

class KillClipBuff(Buff):
    id = 'killclip'
    name = 'Kill Clip'
    flavor = 'Reloading after a kill grants increased damage.'

    duration = 300

    refresh = False
    stacking = False
    unique = True

    mods = [ Mod('damage', 'mult', 0.25, 0.0) ]

    def on_remove(self, context: Context):
        context.target.msg('The glow around your weapon dissipates.')