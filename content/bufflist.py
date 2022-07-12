import random
from typeclasses.components.buff import BaseBuff, Mod
from typeclasses.context import Context

class RampageBuff(BaseBuff):
    key = 'rampage'
    name = 'Rampage'
    flavor = 'Defeating an enemy has filled you with bloodlust.'

    duration = 30

    refresh = True
    stacking = True
    unique = True
    maxstacks = 3

    stack_msg = {
        1: '    You feel a bloodlust welling up inside you.',
        2: '    Your bloodlust calls to you.',
        3: '    All must die.'
    } 

    mods = [ Mod('damage', 'mult', 0.15, 0.15) ]

    def on_apply(self, *args, **kwargs):
        if self.stacks in self.stack_msg.keys(): self.owner.msg(self.stack_msg[self.stacks])

    def on_expire(self, *args, **kwargs):
        self.owner.location.msg('The bloodlust fades.')

class Exploit(BaseBuff):
    key = 'exploit'
    name = 'Exploit'
    flavor = "You are learning your opponent's weaknesses."

    triggers = ['hit']

    duration = 30

    refresh = True
    stacking = True
    unique = True
    maxstacks = 20

    def on_trigger(self, trigger:str, *args, **kwargs):
        chance = self.stacks / 20
        roll = random.random()

        if chance > roll:
            self.owner.buffs.add(Exploited)
            self.owner.location.msg("   An opportunity presents itself!")
            self.owner.buffs.remove('exploit')

    def on_expire(self, *args, **kwargs):
        self.owner.location.msg("The opportunity passes.")

class Exploited(BaseBuff):
    key = 'exploited'
    name = 'Exploited'
    flavor = "You have sensed your target's vulnerability, and are poised to strike."

    duration = 30

    refresh = True
    stacking = False
    unique = True

    mods = [ Mod('damage', 'add', 100) ]

    def after_check(self, *args, **kwargs):
        self.owner.location.msg( "   You exploit your target's weakness!" )
        self.owner.buffs.remove('exploited', delay=0.01)

    def on_remove(self, *args, **kwargs):
        self.owner.location.msg( "You cannot sense your target's weakness anymore." )

class Weakened(BaseBuff):
    key = 'weakened'
    name = 'Weakened'
    flavor = 'An unexplained weakness courses through this person.'

    duration = 30

    refresh = True
    stacking = False
    unique = True

    mods = [ Mod('injury', 'add', 100) ]

class Leeching(BaseBuff):
    key = 'leeching'
    name = 'Leeching'
    flavor = 'Attacking this target fills you with vigor.'

    duration = 30

    refresh = True
    stacking = False
    unique = True

    triggers = ['injury']

    def on_trigger(self, trigger:str, attacker, damage, *args, **kwargs) -> Context:
        if not attacker or not damage: return
        attacker.msg('Debug: Attempting leech.')
        heal = damage * 0.1
        attacker.heal(heal)

class Poison(BaseBuff):
    key = 'poison'
    name = 'Poison'
    flavor = 'A poison wracks this body.'

    duration = 30

    refresh = True
    maxstacks = 5
    unique = True
    tickrate = 5
    dmg = 5

    def on_tick(self, initial=True, *args, **kwargs):
        _dmg = self.dmg * self.stacks
        if initial: self.owner.msg('Initial poison tick')
        if not initial:
            self.owner.location.msg_contents("Poison courses through {actor}'s body, dealing {damage} damage.".format(actor=self.owner.named, damage=_dmg))
            self.owner.combat.damage(_dmg, quiet=True)

class Overflow(BaseBuff):
    key = 'overflow'
    name = 'Overflow'
    flavor = 'Your magazine is overflowing!'

class PropertyBuffTest(BaseBuff):
    key = 'ptest'
    name = 'ptest'
    flavor = 'This person is invigorated.'

    duration = 600
    playtime = True

    refresh = True
    maxStacks = 5
    unique = True

    mods = [Mod('maxhp', 'add', 100, 50)]

class TestBuff(BaseBuff):
    key = 'ttest'
    name = 'ttest'
    flavor = 'This buff has been triggered.'

    triggers = ['test']

    def on_trigger(self, trigger:str, *args, **kwargs):
        print('Triggered test buff!')

class BuffList():
    '''Initialization of buff and effect typeclasses used to apply buffs to players.

    If it's not in this list, it won't be applicable in-game without python access.'''
    # Buffs
    