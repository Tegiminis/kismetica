"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
import time
from typeclasses.item import InventoryHandler, Item
from evennia.utils import utils, lazy_property
import commands.default_cmdsets as default
import commands.destiny_cmdsets as destiny
from typeclasses.buff import BuffHandler, PerkHandler
from evennia import TICKER_HANDLER, DefaultCharacter
from typeclasses.cooldowns import CooldownHandler
from context import Context
import random


import typeclasses.subclass as sc
from typeclasses.content.soldier import Soldier

#region misc handlers

#endregion

class Character(DefaultCharacter):

    # Character class inherited by all characters in the MUD, including NPCs

    # Buff and perk handlers
    @lazy_property
    def buffs(self) -> BuffHandler:
        return BuffHandler(self)

    @lazy_property
    def perks(self) -> PerkHandler:
        return PerkHandler(self)

    @lazy_property
    def cooldowns(self) -> CooldownHandler:
        return CooldownHandler(self)

    def at_object_creation(self):
        
        self.scripts.stop()

        # The dictionaries we use for buffs, perks, and cooldowns. 
        self.db.buffs = {}
        self.db.perks = {}
        self.db.cooldowns = {} 

        self.db.health = 100        # Current health
        self.db.maxHealth = 100     # Max health

        self.db.evasion = 1.0       # Base chance to dodge enemy attacks

    def at_init(self):
        self.ndb.target = None      # Used if you use attack someone or use 'target'

    def damage(self, damage: int, msg=None) -> int:
        '''Applies damage, and returns the damage it applied'''
        damage = self.buffs.check(damage, 'injury')
        self.db.health = max(self.db.health - damage, 0)
        self.msg('You were damaged by %i!' % damage)
    
    def heal(self, heal: int, msg=None) -> int:
        self.db.health = min(self.db.health + heal, self.db.maxHealth)
        self.msg('You healed by %i!' % heal)

    def shoot(self, defender, damage, crit, mult, accuracy, evasion, 
        falloff=4, cqc=1) -> Context:
        '''The most basic attack a character can perform.'''
        
        # The context for our combat. 
        # This holds all sorts of useful info we pass around.
        combat = Context(self, defender)

        _defender: Character = defender

        # Hit calculation and context update
        hit = self._roll_hit(accuracy=accuracy, crit=crit, evasion=evasion)
        combat.hit = hit[0]
        combat.crit = hit[1]

        # Damage calculation
        if combat.hit:
            combat.damage = self._calculate_damage(damage, combat.crit, mult, 
                falloff < _defender.range)

        return combat

    def _roll_hit(
        self,
        accuracy=1.0, crit=2.0, evasion=1.0, cqc=1
        ) -> tuple(bool, bool):
        '''
        Rolls to hit a defender, based on arbitrary accuracy and evasion values.
        
        Args:
            defender: The defender.
            accuracy: The base accuracy value. Typically your weapon's accuracy

        Returns a tuple of bools: was hit, and was crit
        '''

        # Apply all accuracy and crit buffs for attack
        accuracy = self.buffs.check(accuracy, 'accuracy')
        crit = self.buffs.check(crit, 'crit')

        # Random values for hit calculations
        # hit must be > evasion for the player to hit
        hit = random.random()
        dodge = random.random()

        # Modify the hit roll by the accuracy value.
        hit = hit * accuracy
        dodge = dodge * evasion

        # Return a tuple of booleans corresponding to (isHit, isCrit)
        return (hit > dodge, hit > dodge * crit)

    def _calculate_damage(
        self, damage,
        crit=False, critMult=2.0, falloff=False
        ) -> float:
        '''Calculates damage output, unmodified by defender armor.'''

        # Apply falloff, if relevant. Falloff is a flat 20% damage penalty
        if falloff: damage *= 0.8

        # All damage is multiplied by crit
        if crit is True: damage = round(damage * critMult)

        # Apply all attacker buffs to damage
        damage = self.buffs.check(damage, 'damage')

        return round(damage)

    #region calculated properties    
    @property
    def named(self) -> str:
        if self.tags.get('named') is None: return "the " + self.key
        else: return self.key
    
    @property
    def evasion(self):
        _ev = self.buffs.check(self.db.evasion, 'evasion')
        return _ev

    @property
    def maxHealth(self):
        _mh = self.buffs.check(self.db.maxHealth, 'maxhealth')
        return _mh

    @property
    def traits(self):
        _perks = self.perks.traits
        _buffs = self.buffs.traits
        return _perks + _buffs

    @property
    def effects(self):
        _perks = self.perks.effects
        _buffs = self.buffs.effects
        return _perks + _buffs
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
        
        super().at_object_creation()

        self.cmdset.add(default.CharacterCmdSet, permanent=True)
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
        
        # Start with soldier subclass on newly-created characters
        # self.db.subclass = 'soldier'
        # sc.add_subclass(self, Soldier)        
    
    def shoot(self, defender, weapon):
        '''The most basic attack a player can perform. 
        
        Attacker must have a weapon in db.held, otherwise 
        this method will return an error.
        '''
        
        # The context for our combat. 
        # This holds all sorts of useful info we pass around.
        combat = Context(self, defender)

        combat.weapon = self.db.held
        weapon = combat.weapon

        # Variable assignments for legibility
        rpm = weapon.rpm

        # If it has been too soon since your last attack, or you are attacking an invalid target, stop attacking
        if self.cooldowns.isActive('attack') or not defender.is_typeclass('typeclasses.npc.NPC'):
            self.msg("You cannot act again so quickly!")
            return
        
        self.msg((combat.weapon.db.msg['attack'] % ('you',defender.named)).capitalize())

        combat = super().shoot(
            defender, 
            weapon.damage, 
            weapon.critChance, 
            weapon.critMult, 
            weapon.accuracy, 
            defender.evasion, 
            weapon.falloff, 
            weapon.cqc)

        if combat.hit: 
            weapon.buffs.trigger('hit', context=combat)
            self.buffs.trigger('hit', context=combat)

            if combat.crit: 
                self.buffs.trigger('crit', context=combat)
                weapon.buffs.trigger('crit', context=combat)

            combat.damage = defender.damage(combat.damage)
            damage_message += "%i damage!" % combat.damage
            self.msg( damage_message + "\n|n" )

            defender.buffs.trigger('thorns', context=combat)
            defender.buffs.trigger('injury', context=combat)
        else:
            self.msg( weapon.db.msg['miss'] )

        self.cooldowns.start('attack', rpm)
        utils.delay(rpm, self.shoot, defender=defender)
    
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