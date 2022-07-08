"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
import time
import random
from typing import TYPE_CHECKING
from evennia.utils import utils, lazy_property

# Handlers
from typeclasses.components.combat import CombatHandler
from typeclasses.components.buff import BuffHandler, BuffableProperty
from typeclasses.components.cooldowns import CooldownHandler
from typeclasses.item import InventoryHandler, Item

# Commands
import commands.default_cmdsets as default
import commands.destiny_cmdsets as destiny

from evennia import TICKER_HANDLER, DefaultCharacter

if TYPE_CHECKING:
    from typeclasses.npc import NPC
    from typeclasses.weapon import Weapon

class Character(DefaultCharacter):

    # Character class inherited by all characters in the MUD, including NPCs

    # Buff and perk handlers
    @lazy_property
    def buffs(self) -> BuffHandler:
        return BuffHandler(self)

    @lazy_property
    def cooldowns(self) -> CooldownHandler:
        return CooldownHandler(self)

    @lazy_property
    def combat(self) -> CombatHandler:
        return CombatHandler(self)

    maxhp = BuffableProperty(100)
    evasion = BuffableProperty(1)

    mobility = BuffableProperty(3)
    resilience = BuffableProperty(3)
    strength = BuffableProperty(3)
    discipline = BuffableProperty(3)
    recovery = BuffableProperty(3)
    intellect = BuffableProperty(3)

    def at_object_creation(self):
        
        self.scripts.stop()

        self.cmdset.add(default.CharacterCmdSet, permanent=True)

        self.buffs, self.cooldowns, self.combat
        self.maxhp, self.evasion 
        self.mobility, self.resilience, self.strength, self.discipline, self.recovery, self.intellect

        self.db.hp = 100        # Current hp

        super().at_object_creation()

    def at_init(self):
        self.ndb.target = None      # Used if you use attack someone or use 'target'
        self.tags.remove('attacking', category='combat')

    #region calculated properties    
    @property
    def named(self) -> str:
        if self.tags.get('named') is None: return "the " + self.key
        else: return self.key

    @property
    def traits(self):
        _perks = self.perks.traits
        _buffs = self.buffs.traits
        return _perks | _buffs

    @property
    def effects(self):
        _perks = self.perks.effects
        _buffs = self.buffs.effects
        return _perks | _buffs

    #endregion

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
    
    @lazy_property
    def inv(self) -> InventoryHandler:
        return InventoryHandler(self)
    
    def at_object_creation(self):

        self.cmdset.add(destiny.DestinyBasicCmdSet, permanent=True)
        self.cmdset.add(destiny.DestinyBuilderCmdSet, permanent=True)

        self.db.subclasses = {}     # Subclasses dictionary
        self.db.armor = {}          # Armor dictionary
        self.db.skills = {}         # Skills dictionary

        # TickerHandler that fires off the "learn" function
        # TICKER_HANDLER.add(15, self.learn_xp)

        # Are you a "Named" character? Players start out as true.
        self.tags.add("named")

        # Your held weapon. What you shoot with when you use 'attack'
        self.db.held = None

        # XP stats. Current and cap XP. 
        self.db.xp = 0
        self.db.xpCap = 1000
        self.db.xpGain = 10
        self.db.level = 1   

        super().at_object_creation() 

    
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
        _gain = self.buffs.check(self.level * 50, 'gain')
        return _gain

    @property
    def xpCap(self):
        '''The amount of XP you can have "stored". It is "learned" with each tick.'''
        _cap = self.buffs.check(self.level * 1000, 'cap')
        return _cap

    @property
    def level(self):
        '''The combined levels of all a player's subclasses.'''
        subclasses: dict = self.db.subclasses
        _lvl = 0
        for x in subclasses.values(): _lvl += x.get('level', 1)
        return _lvl