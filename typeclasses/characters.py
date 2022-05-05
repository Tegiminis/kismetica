"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
import time
from typing import TYPE_CHECKING

from typeclasses.item import InventoryHandler, Item
from evennia.utils import utils, lazy_property
import commands.default_cmdsets as default
import commands.destiny_cmdsets as destiny
from typeclasses.components.buff import BuffHandler, PerkHandler
from evennia import TICKER_HANDLER, DefaultCharacter
from typeclasses.components.cooldowns import CooldownHandler
from typeclasses.context import Context
import random

if TYPE_CHECKING:
    from typeclasses.npc import NPC
    from typeclasses.weapon import Weapon

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

        self.cmdset.add(default.CharacterCmdSet, permanent=True)

        # The dictionaries we use for buffs, perks, and cooldowns. 
        self.db.buffs = {}
        self.db.perks = {}
        self.db.cooldowns = {} 

        self.db.hp = 100        # Current hp
        self.db.maxHP = 100     # Max hp
        self.db.evasion = 1.0       # Base chance to dodge enemy attacks

        super().at_object_creation()

    def at_init(self):
        self.ndb.target = None      # Used if you use attack someone or use 'target'
        self.tags.remove('attacking', category='combat')

    #region methods
    def damage(self, damage: int, context=None) -> int:
        '''Applies damage, and returns the damage it applied'''
        # Damage check
        damage = self.buffs.check(damage, 'injury')

        if context is not None:
            # Buff triggers
            self.buffs.trigger('thorns', context=context)
            self.buffs.trigger('injury', context=context)

        # Apply damage
        self.db.hp = max(self.db.hp - damage, 0)
        self.msg('You take %i damage!' % damage)

        # If you are out of life, you are out of luck
        self.die()

        return damage

    def die(self, context=None):
        '''This was your life.'''
        self.tags.clear(category='combat')
        self.tags.add('dead', category='state')
        pass
    
    def heal(self, heal: int, msg=None) -> int:
        self.db.hp = min(self.db.hp + heal, self.db.maxHP)
        self.msg('You healed by %i!' % heal)

    def single_attack(
        self, defender, 
        damage, critChance, critMult, accuracy, 
        context: dict = None
        ) -> Context:
        '''The most basic attack a character can perform.
        
        Args:
            defender:   The target you are shooting
            damage:     The source damage value; typically weapon damage
            crit:       Crit chance
            mult:       Crit multiplier
            acc:        Accuracy'''
        
        # self.location.msg_contents("Debug: Attempting a shot")

        # The context for our combat. 
        # This holds all sorts of useful info we pass around.
        if context is None: combat = {'attacker': self, 'defender': defender}
        else: combat = context

        evasion = defender.evasion

        # Hit calculation and context update
        combat = self._roll_hit(accuracy=accuracy, crit=critChance, evasion=evasion, context=combat)

        # Damage calc and buff triggers
        if combat['isHit'] is True:
            combat['damage'] = self._calculate_damage(damage, combat['isCrit'], critMult, False)
            
            self.buffs.trigger('hit', context=combat)
            if combat['isCrit'] is True: self.buffs.trigger('crit', context=combat)

        return combat

    def _roll_hit(
        self,
        accuracy=1.0, crit=2.0, evasion=1.0,
        context:dict=None
        ) -> tuple:
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
        hit = random.random() * 100
        dodge = random.random() * 100

        # Modify the hit roll by the accuracy value.
        hit += accuracy * random.random()
        dodge += evasion * random.random()

        context['isHit'] = hit > dodge
        context['isCrit'] = hit > dodge * crit
        context['hit'] = hit
        context['dodge'] = dodge

        # Return a tuple of booleans corresponding to (isHit, isCrit)
        return context

    def _calculate_damage(
        self, damage,
        crit=False, critMult=2.0, falloff=False
        ) -> float:
        '''Calculates damage output, unmodified by defender armor.'''

        # All damage is multiplied by crit
        if crit is True: damage = round(damage * critMult)

        # Apply all attacker buffs to damage
        damage = self.buffs.check(damage, 'damage')

        return round(damage)
    #endregion

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
    def maxHP(self):
        _mh = self.buffs.check(self.db.maxHP, 'maxHP')
        return _mh

    @property
    def range(self):
        _mh = self.buffs.check(self.db.range, 'range')
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

    def basic_attack(self, defender, auto=True, sim=False):
        '''The most basic ranged attack a player can perform. 
        
        Attacker must have a weapon in db.held, otherwise 
        this method will return an error.
        '''
        if not self.tags.has('attacking', 'combat'): return
        
        defender: NPC = defender

        # Can't attack something that isn't an NPC (for now)
        if not defender.is_typeclass('typeclasses.npc.NPC'): 
            self.msg("You can only attack NPCs!")
            return

        # Your target changed rooms; gave you the slip
        if defender.location != self.location:
            self.msg("Your target has slipped away from you!")
            return

        weapon: Weapon = self.db.held

        # Can't fire an empty gun!
        if weapon.ammo <= 0:
            self.msg("Your weapon is out of ammo!")
            return

        # Variable assignments for legibility
        _rpm = weapon.rpm

        # If it has been too soon since your last attack, figure out when you can attack next, and delay to then
        if self.cooldowns.find('attack'): 
            _tl = self.cooldowns.time_left('attack')
            utils.delay(_tl, self.basic_attack, defender=defender)
            return
        
        # Default messages for hits and crits, depending on the damage type
        # (bullet, plasma, slashing, blunt)
        default_msg = {
            "bullet": {
                "hit": ["%s staggers under the flurry of bullets.", None],
                "crit": ["Blood spurts uncontrollably from newly-apportioned wounds!", None]
            },
            "fusion": {
                "hit": ["Bolts of multicolored plasma singe %s's armor."],
                "crit": ["Molten matter fuses to flesh as %s screams in agony!"]
            }

        }

        # The context dictionary for combat, used to pass combat data around to other functions
        combat = {
            'attacker': self,
            'defender': defender
        }

        # Messaging for yourself and the room
        self.msg( weapon.db.msg['self'] % ( weapon.named, defender.named ) )
        self.location.msg_contents( weapon.db.msg['attack'] % (self.named, weapon.named, defender.named), exclude=self)

        # Multishot loop
        for x in range(max(1, weapon.shots)):
            
            # Bundle weapon stats and pass them to the "single shot" attack method
            weapon_stats = weapon.WeaponData
            combat = self.single_attack(defender, **weapon_stats, context=combat)

            if x <= 0: self.msg(f"  HIT: +{int(combat['hit'])} vs EVA: +{int(combat['dodge'])}")

            if combat['isHit'] is True: 
                combat['damage'] = defender.damage(combat['damage'], context=combat)

                weapon.buffs.trigger('hit', context=combat)
                if combat['isCrit'] is True: weapon.buffs.trigger('crit', context=combat)

                defender.buffs.trigger('thorns', context=combat)
                defender.buffs.trigger('injury', context=combat)

                if combat['isHit'] is True: self.msg( "    ... %i damage! |n\n" % combat['damage'] )

                msgHit = random.choice(default_msg['bullet']['hit'])
                msgCrit = random.choice(default_msg['bullet']['crit'])
            else:
                if x <= 0: self.msg('    ... Miss!')
                break
    
        if msgHit: self.msg("    " +  (msgHit % defender.named).capitalize() + "|n\n")
        if msgCrit: self.msg("    " +  msgCrit.capitalize() + "|n\n")

        weapon.db.ammo -= 1
        self.cooldowns.start('attack', _rpm)
        
        if auto: utils.delay(_rpm, self.basic_attack, defender=defender)
    
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