"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
from typeclasses.item import Item
from evennia.utils import utils
import commands.default_cmdsets as default
import commands.destiny_cmdsets as destiny
import typeclasses.buffhandler as bh
from evennia import TICKER_HANDLER, DefaultCharacter


import typeclasses.subclass as sc
from typeclasses.content.soldier import Soldier

class Character(DefaultCharacter):

    # Character class inherited by all characters in the MUD. Stats here will be used by every character in the game.    

    def at_object_creation(self):
        
        self.scripts.stop()

        # The dictionaries we use for buffs, perks, effects, traits, and cooldowns. All characters have these, even NPCs.
        self.db.buffs = {}
        self.db.perks = {}
        self.db.cooldowns = {} 

        self.db.health = 100        # Current health
        self.db.maxHealth = 100     # Max health

        self.db.evasion = 1.0       # Base chance to dodge enemy attacks

        self.db.named = False       # If false, name will be prefixed by "the"

    def at_init(self):
        self.ndb.target = None      # Used if you use attack someone or use 'target'

    def damage_health(self, damage: int, msg=None):
        self.db.health = max(self.db.health - damage, 0)
        self.msg('You were damaged by %i!' % damage)
    
    def add_health(self, heal: int, msg=None):
        self.db.health = max(self.db.health + heal, 0)
        self.msg('You healed by %i!' % heal)
    
    @property
    def named(self) -> str:
        if self.db.named is False: return "the " + self.key
        else: return self.key
    
    @property
    def evasion(self):
        _ev = bh.check_stat_mods(self, self.db.evasion, 'evasion')
        return _ev

    @property
    def maxHealth(self):
        _mh = bh.check_stat_mods(self, self.db.maxHealth, 'maxhealth')
        return _mh

    @property
    def traits(self):
        _perks = [x for x in self.db.perks.values() if x['ref']().mods ]
        _buffs = [x for x in self.db.buffs.values() if x['ref']().mods ]
        return _perks + _buffs

    @property
    def effects(self):
        _perks = [x for x in self.db.perks.values() if x['ref']().trigger ]
        _buffs = [x for x in self.db.buffs.values() if x['ref']().trigger ]
        return _perks + _buffs

    """
    The Character defaults to reimplementing some of base Object's hook methods with the
    following functionality:

    at_basetype_setup - always assigns the DefaultCmdSet to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead).
    at_after_move(source_location) - Launches the "look" command after every move.
    at_post_unpuppet(account) -  when Account disconnects from the Character, we
                    store the current location in the pre_logout_location Attribute and
                    move it to a None-location so the "unpuppeted" character
                    object does not need to stay on grid. Echoes "Account has disconnected"
                    to the room.
    at_pre_puppet - Just before Account re-connects, retrieves the character's
                    pre_logout_location Attribute and move it back on the grid.
    at_post_puppet - Echoes "AccountName has entered the game" to the room.

    """

    pass

class PlayerCharacter(Character):

    # The module we use for all player characters. This contains player-specific stats.

    def add_xp(self, xp: int):
        '''Adds XP to this object, respecting all capacity rules.'''
        _xp = bh.check_stat_mods(self, xp, 'xp')
        self.db.xp = min(self.db.xp + _xp, self.xpCap)

    def learn_xp(self):
        '''Learns XP, permanent adding it to your current subclass' pool. If your subclass is capped or you have no xp, nothing happens.
        
        Returns the amount of XP you learned.'''
        subclasses : dict = self.db.subclasses
        subclass : str = self.db.subclass

        if self.db.xp <= 0: return
        if subclass not in subclasses.keys(): return

        _learn = min(self.db.xp, self.xpGain)

        subclasses[subclass]['xp'] += _learn
        self.db.xp -= _learn

        sc.check_for_level(self, subclass)

        return _learn
    
    def at_object_creation(self):
        
        super().at_object_creation()

        self.cmdset.add(default.CharacterCmdSet, permanent=True)
        self.cmdset.add(destiny.DestinyBasicCmdSet, permanent=True)
        self.cmdset.add(destiny.DestinyBuilderCmdSet, permanent=True)

        self.db.subclasses = {}     # Subclasses dictionary
        self.db.armor = {}          # Armor dictionary
        self.db.skills = {}         # Skills dictionary

        # TickerHandler that fires off the "learn" function
        TICKER_HANDLER.add(15, self.learn_xp)

        # Are you a "Named" character? Players start out as true.
        self.db.named = True

        # Your held weapon. What you shoot with when you use 'attack'
        self.db.held = None

        # XP stats. Current and cap XP. 
        self.db.xp = 0
        self.db.xpCap = 1000
        self.db.xpGain = 10
        self.db.level = 1
        
        # Start with soldier subclass on newly-created characters
        self.db.subclass = 'soldier'
        sc.add_subclass(self, Soldier)        
    
    @property
    def weight(self):
        '''The character's current weight, taking into account all held items.'''
        _weight = 0

        for x in self.contents: 
            if utils.inherits_from(x, Item):
                x: Item
                _weight += x.db.weight
        
        return _weight

    @property
    def xpGain(self):
        '''The amount of XP you learn from your cap with each tick.'''
        _gain = bh.check_stat_mods(self, self.level * 50, 'gain')
        return _gain

    @property
    def xpCap(self):
        '''The amount of XP you can have "stored". It is "learned" with each tick.'''
        _cap = bh.check_stat_mods(self, self.level * 1000, 'cap')
        return _cap

    @property
    def level(self):
        '''The combined levels of all a player's subclasses.'''
        subclasses: dict = self.db.subclasses
        _lvl = 0
        for x in subclasses.values(): _lvl += x.get('level', 1)
        return _lvl