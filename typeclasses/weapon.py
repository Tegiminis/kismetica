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

class WeaponData():
    """An object to hold weapon data while passing it between the weapon and character functions. Condenses the game weapon object into simpler form!"""


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
        """Reloads this weapon and returns the amount of ammo that was reloaded."""
        _return = 0

        # Get the weapon's ammo, mag (max ammo), and figure out how much you are reloading
        _ammo = self.ammo
        _mag = self.mag
        _toreload = _mag - _ammo

        # Primary weapons don't use reserves, so if this is a primary ammo weapon, skip all the reserves stuff!
        if ('primary', 'ammo') in self.tags.all(True): 
            _return = _toreload
            self.db.ammo = _mag
            return _return

        # Find and check reserve count
        _reserves = self.db.reserves
        if _reserves <= 0: return 0
        
        # If you have to reload more than you have in reserves, then only reload what you can. Otherwise, top off.
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
        self.db.ammo = 5        # Amount of shots you can make
        self.db.mag = 5         # Mag size; what you reload to
        self.db.reserves = 0    # Amount of ammo you have in reserve
        self.db.inventory = 0   # Amount of ammo you can hold in reserve
        
        # Damage stats
        self.db.damage = 10         # Base damage
        self.db.stability = 10      # Increases low damage bracket
        self.db.range = 10          # Increases upper damage bracket
        self.db.penetration = 1     # Flat armor penetration value

        # Hit/shot stats
        self.db.accuracy = 1.0      # Percent of weapon proficiency used for accuracy
        self.db.spread = 1.0        # Chance to attack multiple targets
        self.db.combo = 1.0         # Chance to attack the first target multiple times

        # Speed stats for doing particular actions (forces cooldown)
        self.db.equip = 20
        self.db.reload = 15
        self.db.rpm = 5

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
        '''Gives you an adjective string determined by the magazine fill percentage.'''

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

    #region properties
 
    @property
    def WeaponData(self):
        """Returns a dictionary consisting of a randomized damage value and common attributes used for character attack functions.
        Passed to character attack functions as kwargs usually."""
        _dict = {
            "damage": self.randomized_damage,
            "critChance": self.critChance,
            "critMult": self.critMult,
            "accuracy": self.accuracy,
        }
        return _dict

    #region damage
    @property
    def damage(self):
        '''Returns a base damage value, buffed by mods.'''
        _modifiedDmg = self.buffs.check(self.db.damage, 'damage')
        return _modifiedDmg

    @property
    def randomized_damage(self):
        '''Returns a randomized damage value.'''
        _dmg = random.randint(self.damageMin, self.damageMax)
        return _dmg

    @property
    def damageMin(self):
        '''Ranges from 50% base damage to 100% base damage, depending on stability'''
        _dmg = self.damage
        return int( _dmg * (0.5 + (0.5 * (self.stability / 100))) )

    @property
    def damageMax(self):
        '''Ranges from 150% base damage to 200% base damage, depending on range.'''
        _dmg = self.damage
        return int( _dmg * (1.5 + (0.5 * (self.range / 100))) )

    @property
    def accuracy(self):
        '''Base accuracy modified by buffs.'''
        _acc = self.buffs.check(self.db.accuracy, 'accuracy')
        return _acc

    @property
    def range(self):
        '''Base range modified by buffs.'''
        _rng = self.buffs.check(self.db.range, 'range')
        return _rng

    @property
    def stability(self):
        '''Base stability modified by buffs.'''
        _stab = self.buffs.check(self.db.stability, 'stability')
        return _stab

    @property
    def critChance(self):
        '''Base critical chance modified by buffs.'''
        _prec = self.buffs.check(self.db.critChance, 'critchance')
        return _prec

    @property
    def critMult(self):
        '''Base critical damage multiplier modified by buffs.'''
        _hs = self.buffs.check(self.db.critMult, 'critmult')
        return _hs

    @property
    def shots(self):
        '''Returns the number of shots this weapon will fire. Based on combo stat.'''
        _combo = self.buffs.check(self.db.combo, 'combo')
        _shots = round(random.random() * _combo)
        return _shots

    @property
    def penetration(self):
        '''Returns the number of shots this weapon will fire.'''
        _pen = self.buffs.check(self.db.penetration, 'penetration')
        return _pen

    @property
    def spread(self):
        '''Returns the number of shots this weapon will fire.'''
        _sprd = self.buffs.check(self.db.spread, 'spread')
        return _sprd
    #endregion
    #region ammo
    @property
    def ammo(self):
        '''This weapon's current ammo.'''
        return self.db.ammo
    @ammo.setter
    def ammo(self, amount):
        self.db.ammo = amount

    @property
    def mag(self):
        '''The ammo count you reload to, modified by buffs. Only applies at time of reload.'''
        _mag = self.buffs.check(self.db.mag, 'mag')
        return _mag
    #endregion
    #region action times
    @property
    def reload(self):
        '''Base reload round time modified by buffs.'''
        _rl = self.buffs.check(self.db.reload, 'reload')
        return _rl

    @property
    def equip(self):
        '''Base equip round time modified by buffs. Applies to stowing and equipping.'''
        _eq = self.buffs.check(self.db.equip, 'equip')
        return _eq

    @property
    def rpm(self):
        '''Base round time modified by buffs.'''
        _rpm = self.buffs.check(self.db.rpm, 'rpm')
        return _rpm    
    #endregion
    #region handler returns
    @property
    def traits(self):
        '''All traits on the object, both perks and buffs.'''
        _buffs = self.buffs.traits
        _perks = self.perks.traits
        return _perks + _buffs

    @property
    def effects(self):
        '''All effects on the object, both perks and buffs.'''
        _perks = self.perks.effects
        _buffs = self.buffs.effects
        return _perks + _buffs
    #endregion
    #endregion