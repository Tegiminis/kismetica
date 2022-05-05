from typeclasses.context import Context
from typeclasses.components.buff import Buff, Perk, Mod
import content.bufflist as bl

class RampagePerk(Perk):
    key = 'rampage'
    name = 'Rampage'
    flavor = 'Kills with this weapon temporarily increase its damage.'

    trigger = 'hit'

    stack_msg = {
        1: '    You feel a bloodlust welling up inside you.',
        2: '    Your bloodlust calls to you.',
        3: '    All must die.'
    } 

    def on_trigger(self):
        bc: Context = context.weapon.buffs.add(bl.RampageBuff)
        if bc.buffStacks in self.stack_msg: context.weaponOwner.msg( self.stack_msg[bc.buffStacks] )
        return bc

class ExploitPerk(Perk):

    key = 'exploit'
    name = 'Exploit'
    flavor = 'Shooting an enemy with this weapon allows you to find their weakness.'

    trigger = 'hit'

    stack_msg = {
        1:"    You begin to notice flaws in your opponent's defense.",
        10:"    You're certain you've found a weakness. You just need more time.",
        20:"    You've discovered your opponent's weak spot."
    }

    trigger_msg = ''

    def on_trigger(self):
        if self.owner.buffs.find(bl.Exploited): return None
        self.owner.buffs.add(bl.Exploit)
        if self.stacks in self.stack_msg: self.owner.location.msg( self.stack_msg[self.stacks] )

class WeakenPerk(Perk):
    key = 'weaken'
    name = 'Weaken'
    flavor = 'Shooting an enemy with this weapon increases the damage they take from all sources.'

    trigger = 'hit'

    def on_trigger(self):
        self.context['target'].buffs.add(bl.Poison)

class LeechRoundPerk(Perk):
    key = 'leechround'
    name = 'Leech Round'
    flavor = 'Primes enemies with a leeching worm which heals attackers.'

    trigger = 'hit'

    def on_trigger(self):
        context.origin.buffs.add(bl.Leeching)

class ThornsPerk(Perk):
    key = 'thorns'
    name = 'Thorns'
    flavor = 'Damages attackers'

    trigger = 'thorns'

    def on_trigger(self):
        context.origin.damage_health(context.damage * 0.1)

class PerkList():
    rampage = RampagePerk
    exploit = ExploitPerk
    weaken = WeakenPerk
    leechround = LeechRoundPerk
