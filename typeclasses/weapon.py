import random
import time
from typing import TYPE_CHECKING

from typeclasses.context import Context
from typeclasses.components.cooldowns import CooldownHandler
from typeclasses.objects import Object
from typeclasses.components.buff import BaseBuff, BuffHandler, BuffableProperty
from evennia.utils import lazy_property
from evennia import Command as BaseCommand
from evennia import CmdSet

if TYPE_CHECKING:
    from typeclasses.characters import Character

class FusionCharging(BaseBuff):
    key = 'fusioncharging'
    isVisible = False
    unique = True
    duration = 5
    
    def on_expire(self, *args, **kwargs) -> Context:
        self.owner.buffs.add(FusionCharged)
        pass
        
class FusionCharged(BaseBuff):
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

    def on_expire(self, *args, **kwargs):
        player: Character = self.owner.location
        _dmg = round(player.db.maxHP * 0.75)
        player.msg("Your %s explodes, mangling your hands and filling your lungs with searing plasma!" % self.owner)
        player.damage(_dmg)

    def on_tick(self, *args, **kwargs):
        _tn = self.ticknum
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

    mag = BuffableProperty(10)
    inventory = BuffableProperty(0)

    damage = BuffableProperty(10)
    stability = BuffableProperty(10)
    range = BuffableProperty(10)
    penetration = BuffableProperty(1)

    accuracy = BuffableProperty(50)
    spread = BuffableProperty(1.0)
    combo = BuffableProperty(1.0)

    equip = BuffableProperty(20)
    reload = BuffableProperty(15)
    rpm = BuffableProperty(5)

    critchance = BuffableProperty(2)
    critmult = BuffableProperty(2)

    def at_object_creation(self):
        "Called when object is first created"

        self.cmdset.add(WeaponCmdSet, permanent=True)
        self.locks.add('call:equipped()')
        self.tags.add("primary", category="ammo")

        # Ammo stats
        self.db.ammo = 5        # Amount of shots you can make
        self.mag         # Mag size; what you reload to
        self.db.reserves = 0    # Amount of ammo you have in reserve
        self.inventory   # Amount of ammo you can hold in reserve
        
        # Damage stats
        self.damage         # Base damage
        self.stability      # Increases low damage bracket
        self.range          # Increases upper damage bracket
        self.penetration     # Flat armor penetration value

        # Hit/shot stats
        self.accuracy    # Percent of weapon proficiency used for accuracy
        self.spread      # Chance to attack multiple targets
        self.combo       # Chance to attack the first target multiple times

        # Speed stats for doing particular actions (forces cooldown)
        self.equip
        self.reload
        self.rpm

        # Crit chance and multiplier
        self.critchance
        self.critmult

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
    def weapondata(self):
        """Returns a dictionary consisting of a randomized damage value and common attributes used for character attack functions.
        Passed to character attack functions as kwargs usually."""
        _dict = {
            "damage": self.randomized_damage,
            "critChance": self.critchance,
            "critMult": self.critmult,
            "accuracy": self.accuracy,
        }
        return _dict

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
    def shots(self):
        '''Returns the number of shots this weapon will fire. Based on combo stat.'''
        _combo = self.combo
        _shots = round(random.random() * _combo)
        return _shots

    @property
    def ammo(self):
        '''This weapon's current ammo.'''
        return self.db.ammo
    @ammo.setter
    def ammo(self, amount):
        self.db.ammo = amount

    @property
    def traits(self):
        '''All traits on the object, both perks and buffs.'''
        _buffs = self.buffs.traits
        return _buffs

    @property
    def effects(self):
        '''All effects on the object, both perks and buffs.'''
        _buffs = self.buffs.effects
        return _buffs