"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
import commands
from evennia import DefaultCharacter
import typeclasses.destiny_scripts as dscript

# destiny_rules is the rules module that contains all combat calculations, dicts, and other important doodads
from world import destiny_rules

class Character(DefaultCharacter):

    # Character class inherited by all characters in the MUD. Stats here will be used by every character in the game.

    def at_object_creation(self):
        
        self.scripts.stop()

        # Health values
        # [Current, Max]
        self.db.health = {"current":100, "max":100}

        # Are you a "Named" character? All characters start as false, except players, who start true. 
        # Must be manually enabled for named NPCs
        self.db.named = False

        # Shield values
        # [Current, Max, Base Regen, Delay Until Regen, Last Time Hit, Element]
        self.db.shield = {"current":100, "max":100, "regen":10, "delay":5, "lasthit":0, "element":"neutral"}

        # The character's "room depth", or how far they are into the room
        # At the moment, your room_depth is 0 when you enter a room, and can increase as you take movement actions
        # Good compromise between simplicity and allowing for range mechanics
        # Distance between objects is calculated using room_depth
        # room_depth's unit value is "meters", not that it matters
        self.db.room_depth = 0.0

        if not self.scripts.get('shield_regen'):
            self.scripts.add(dscript.ShieldRegen)

    def at_init(self):
        # Used if you use attack someone or use 'target'
        self.ndb.target = 0


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

    def at_object_creation(self):
        
        super().at_object_creation()

        self.cmdset.add(commands.default_cmdsets.CharacterCmdSet, permanent=True)
        self.cmdset.add(commands.destiny_cmdsets.DestinyBasicCmdSet, permanent=True)
        self.cmdset.add(commands.destiny_cmdsets.DestinyBuilderCmdSet, permanent=True)

        # Are you a "Named" character? Players start out as true.
        self.db.named = True

        # Your held weapon. What you shoot with when you use 'attack'
        self.db.equipped_held = 'kinetic'

        # List of character's equipped weapons
        # [Kinetic, Energy, Power]
        self.db.equipped_weapons = {"kinetic":None, "energy":None, "power":None}

        # List of character's equipped armor
        # [Head, Arms, Body, Legs, Class]
        self.db.equipped_armor = {"head":None, "arms":None, "body":None, "legs":None, "class":None}

        # Are you capable of being attacked, aka in PvP?
        self.db.crucible = False

        # Proficiencies. They determine what access to skills you have. 
        # Each proficiency is a linear level progression
        self.db.proficiency = {
            'rifle': {'level':0, 'xp':0}
        }
        
        # Cooldowns!
        self.db.cooldowns = {'basic':0, 'swap':0, 'equip':0, 'move':0}

    pass