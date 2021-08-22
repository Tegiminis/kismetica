"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
import commands.default_cmdsets as default
import commands.destiny_cmdsets as destiny
import typeclasses.handlers.buffhandler as bh
from evennia import DefaultCharacter

class Character(DefaultCharacter):

    # Character class inherited by all characters in the MUD. Stats here will be used by every character in the game.

    @property
    def evasion(self):
        _ev = bh.check_stat_mods(self, self.db.evasion, 'evasion')
        return _ev

    @property
    def maxHealth(self):
        _mh = bh.check_stat_mods(self, self.db.maxHealth, 'maxhealth')
        return _mh

    def at_object_creation(self):
        
        self.scripts.stop()

        # The dictionaries we use for buffs, perks, effects, and traits
        self.db.buffs = {}
        self.db.perks = {}
        self.db.effects = {}
        self.db.traits = {}

        # Health values
        self.db.health = 100
        self.db.maxHealth = 100

        self.db.evasion = 1.0

        # Are you a "Named" character? All characters start as false, except players, who start true. 
        # Must be manually enabled for named NPCs
        self.db.named = False

    def at_init(self):
        # Used if you use attack someone or use 'target'
        self.ndb.target = 0

    @property
    def name(self) -> str:
        if self.db.named is False: return "the " + self.key
        else: return self.key


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

    weightMax = 100
    
    def at_object_creation(self):
        
        super().at_object_creation()

        self.cmdset.add(default.CharacterCmdSet, permanent=True)
        self.cmdset.add(destiny.DestinyBasicCmdSet, permanent=True)
        self.cmdset.add(destiny.DestinyBuilderCmdSet, permanent=True)

        # Are you a "Named" character? Players start out as true.
        self.db.named = True

        # Your held weapon. What you shoot with when you use 'attack'
        self.db.held = None

        # List of character's equipped armor. Equipped armor will replace anything in the same slot.
        self.db.armor = {}

        # Proficiencies. They determine what access to skills you have. 
        # Each proficiency is a linear level progression
        self.db.skills = {
            'rifle': {'level':0, 'xp':0}
        }
        
        # Cooldowns!
        self.db.cooldown = 0
    
    @property
    def weight(self):
        return self.myweight

    pass