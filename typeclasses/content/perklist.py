from typeclasses.context import Context
from typeclasses.buff import Buff, Perk, Mod
import typeclasses.buffhandler as bh
import typeclasses.content.bufflist as bl

class RampagePerk(Perk):
    id = 'rampage'
    name = 'Rampage'
    flavor = 'Kills with this weapon temporarily increase its damage.'

    trigger = 'hit'

    stack_msg = {
        1: 'You feel a bloodlust welling up inside you.',
        2: 'Your bloodlust calls to you.',
        3: 'All must die.'
    } 

    def on_trigger(self, context: Context):
        context.origin.location.msg("Debug Owner Context: " + str(context.owner))
        bc: Context = bh.add_buff(context.origin, context.origin, bl.RampageBuff)
        if bc.stacks in self.stack_msg: context.owner.msg( self.stack_msg[bc.stacks] )
        return bc

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

    def on_trigger(self, context: Context) -> Context:
        
        if bh.check_for_buff(context.origin, bl.Exploited): return None
        bc: Context = bh.add_buff(context.origin, context.origin, bl.Exploit)
        if bc.stacks in self.stack_msg: context.owner.msg( self.stack_msg[bc.stacks] )
        return bc

class WeakenPerk(Perk):
    id = 'weaken'
    name = 'Weaken'
    flavor = 'Shooting an enemy with this weapon increases the damage they take from all sources.'

    trigger = 'hit'

    def on_trigger(self, context: Context) -> Context:
        bh.add_buff(context.origin, context.target, bl.Weakened)

class LeechRoundPerk(Perk):
    id = 'leechround'
    name = 'Leech Round'
    flavor = 'Primes enemies with a leeching worm which heals attackers.'

    trigger = 'hit'

    def on_trigger(self, context: Context) -> Context:
        bh.add_buff(context.origin, context.target, bl.Leeching)

class ThornsPerk(Perk):
    id = 'thorns'
    name = 'Thorns'
    flavor = 'Damages attackers'

    trigger = 'thorns'

    def on_trigger(self, context: Context) -> Context:
        context.origin.damage_health(context.damage * 0.1)

class PerkList():
    rampage = RampagePerk
    exploit = ExploitPerk
    weaken = WeakenPerk
    leechround = LeechRoundPerk
