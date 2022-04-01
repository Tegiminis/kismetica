import random
import time
from typing import TYPE_CHECKING

from typeclasses.context import Context
from typeclasses.components.cooldowns import CooldownHandler
from typeclasses.objects import Object
from typeclasses.components.buff import Buff, BuffHandler, PerkHandler
from evennia.utils import lazy_property
from evennia import Command as BaseCommand
from evennia import CmdSet

if TYPE_CHECKING:
    from typeclasses.characters import Character

class FusionCharging(Buff):
    key = 'fusioncharging'
    isVisible = False
    unique = True
    duration = 5
    
    def on_expire(self, context: Context) -> Context:
        self.owner.buffs.add(FusionCharged)
        pass
        

class FusionCharged(Buff):
    key = 'fusioncharged'
    
    isVisible = False
    duration = 30
    unique = True

    ticking = True
    tickrate = 5

    tick_msg = {
        1:"Your %s vibrates in your hands, ready to unleash.",
        3:"The barrel of your %s begins to glow, and the vibrating grows stronger.",
        5:"You hear a low whine as heat radiates from the chamber of your %s, scalding your hands."
    }

    def on_expire(self, context: Context) -> Context:
        player: Character = self.owner.location
        _dmg = round(player.db.maxHP * 0.75)
        player.msg("Your %s explodes, mangling your hands and filling your lungs with searing plasma!" % self.owner)
        player.damage(_dmg)

    def on_tick(self, context: Context) -> Context:
        _tn = self.ticknum(context.buffStart)
        if _tn in self.tick_msg.keys():
            self.owner.location.msg(self.tick_msg[_tn] % self.owner)

class CmdReload(BaseCommand):
    """
    Reloads this weapon if it is in the equipped slot.

    Usage:
      rel

    """
    key = "rel"
    locks = ""

    def parse(self):
        pass

    def func(self):
        _caller = self.caller
        _obj = self.obj
        _str = self.obj._reload()        
        _caller.msg("You slap a new mag into your %s." % _obj)
        _caller.location.msg_contents("%s reloads their %s." % (_caller, _obj), exclude=_caller)
        return

class CmdCharge(BaseCommand):
    """
    Charges this weapon. Used on fusion rifles only

    Usage:
      charge

    """
    key = "charge"
    locks = "cmd:tagged(fusion)"

    def parse(self):
        pass

    def func(self):
        _caller = self.caller
        _obj = self.obj

        if not _obj.tags.has('fusion'): 
            _caller.msg("You attempt to charge your %s, and it doesn't work! Perhaps it needs to be a fusion weapon." % _obj)
            return 
        _obj.buffs.add(FusionCharging)
        _caller.msg("You begin to charge your %s." % _obj)
        _caller.location.msg_contents("%s charges their %s." % (_caller, _obj), exclude=_caller)
        return

class WeaponCmdSet(CmdSet):
        
    key = "WeaponCmds"

    def at_cmdset_creation(self):     
        self.add(CmdReload())
        self.add(CmdCharge())

class Weapon(Object):
    """
    A weapon that can be used by player characters.
    """

    @lazy_property
    def buffs(self) -> BuffHandler:
        return BuffHandler(self)

    @lazy_property
    def perks(self) -> PerkHandler:
        return PerkHandler(self)
    
    def _reload(self) -> int:
        """Reloads this weapon and returns the amount of ammo left."""
        _return = 0

        _ammo = self.db.ammo
        _mag = self.db.mag
        _toreload = _mag - _ammo

        if ('primary', 'ammo') in self.tags.all(True): 
            _return = _toreload
            self.db.ammo = _mag
            return _return

        _reserves = self.db.reserves
        if _reserves <= 0: return 0
        
        if _toreload > _reserves: 
            _return = _reserves
            self.db.ammo += _reserves
            self.db.reserves = 0
        else:
            _return = _toreload
            self.db.ammo += _toreload
            self.db.reserves -= _toreload

        return _return

    def at_object_creation(self):
        "Called when object is first created"

        self.cmdset.add(WeaponCmdSet, permanent=True)
        self.locks.add('call:equipped()')
        self.tags.add("primary", category="ammo")
        
        self.db.buffs = {}
        self.db.perks = {}

        # Ammo stats
        self.db.ammo = 5   # Amount of shots you can make
        self.db.mag = 5    # Mag size; what you reload to
        self.db.reserves = 0
        self.db.inventory = 0
        
        # Damage stats
        self.db.damage = 10
        self.db.stability = 10

        # Hit/shot stats
        self.db.shots = 1
        self.db.accuracy = 1.0

        # Speed stats for doing particular actions (forces cooldown)
        self.db.equip = 20
        self.db.reload = 15
        self.db.rpm = 5

        # Range stats. 
        self.db.range = 10      # Increases upper damage bracket
        self.db.cqc = 1         # Decrease accuracy when enemy range is lower
        self.db.falloff = 3     # Decrease damage when enemy range is higher

        # Crit chance and multiplier
        self.db.critChance = 2.0
        self.db.critMult = 2.0

        # Messages for your weapon.
        # Most weapons only have self (what you see when you attack) and attack (what the room sees when you attack)
        # Exotics and altered weapons might have unique messages
        self.db.msg = {
            'self':'You shoot your %s at %s.',
            'attack': '%s shoots their %s at %s.'
            }

        # Gun's rarity. Common, Uncommon, Rare, Legendary, Unique, Exotic. Dictates number of perks when gun is rolled on.
        self.db.rarity = 1
    
    @property
    def named(self):
        if self.tags.get('named') is None: return "the " + self.key
        else: return self.key

    @property
    def magcheck(self):

        _str = ""
        _perc = self.db.ammo / self.db.mag

        if _perc > 1.0: _str = "overflowing"
        elif _perc == 1.0: _str = "topped off"
        elif _perc > 0.8: _str = "nearly full"
        elif _perc > 0.6: _str = "lightly used"
        elif _perc > 0.4: _str = "roughly half"
        elif _perc > 0.2: _str = "running low"
        elif _perc > 0: _str = "almost out"
        elif _perc <= 0: _str = "concerningly empty"

        return _str
        pass

    #region properties
    @property
    def ammo(self):
        # self.db.ammo = min(self.db.ammo, self.maxAmmo)
        return self.db.ammo
    
    @property
    def damage(self):
        _dmg = random.randint(self.damageMin, self.damageMax)
        # self.location.msg('Debug Randomized Damage: ' + str(_dmg))
        _modifiedDmg = self.buffs.check(_dmg, 'damage')
        # self.location.msg('Debug Modified Damage: ' + str(_modifiedDmg - _dmg))
        return _modifiedDmg

    @property
    def damageMin(self):
        _min = self.db.damage / 2
        return int( _min + ( _min * (self.stability / 100) ) )

    @property
    def damageMax(self):
        _dmg = self.db.damage
        _max = _dmg / 2
        return int( _dmg + _max + (_max * (self.range / 100)) )

    @property
    def accuracy(self):
        _acc = self.buffs.check(self.db.accuracy, 'accuracy')
        return _acc

    @property
    def range(self):
        _rng = self.buffs.check(self.db.range, 'range')
        return _rng

    @property
    def stability(self):
        _stab = self.buffs.check(self.db.stability, 'stability')
        return _stab

    @property
    def maxAmmo(self):
        _mag = self.buffs.check(self.db.mag, 'mag')
        return _mag

    @property
    def equip(self):
        _eq = self.buffs.check(self.db.equip, 'equip')
        return _eq

    @property
    def reload(self):
        _rl = self.buffs.check(self.db.reload, 'reload')
        return _rl

    @property
    def rpm(self):
        _rpm = self.buffs.check(self.db.rpm, 'rpm')
        return _rpm

    @property
    def cqc(self):
        _cqc = self.buffs.check(self.db.cqc, 'cqc')
        return _cqc

    @property
    def falloff(self):
        '''The range at which you see a 20% damage penalty. This must be higher
        than a defender's range in order to avoid damage penalty. Having a
        high range stat can buff this by one tier.'''
        _fo = self.db.falloff
        _fo += int(self.range / 90)
        _fo = self.buffs.check(self.db.falloff, 'falloff')
        return _fo

    @property
    def critChance(self):
        _prec = self.buffs.check(self.db.critChance, 'critchance')
        return _prec

    @property
    def critMult(self):
        _hs = self.buffs.check(self.db.critMult, 'critmult')
        return _hs

    @property
    def shots(self):
        _shots = self.buffs.check(self.db.shots, 'shots')
        return _shots
    
    @property
    def traits(self):
        _buffs = self.buffs.traits
        _perks = self.perks.traits
        return _perks + _buffs

    @property
    def effects(self):
        _perks = self.perks.effects
        _buffs = self.buffs.effects
        return _perks + _buffs
    #endregion