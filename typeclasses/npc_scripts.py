import random
import time
from typeclasses.scripts import Script
from evennia import utils

class AIStateBasic(Script): 
    """
    A script which acts as a basic state machine for any non-puppeted character it is attached to.

    This script is actively placed on all NPCs at init.
    Default AI actions include attacking with ranged and melee weapons, and patrolling
    This state machine also handles the AI dying and reviving, among other things.
    """
    def at_script_creation(self):
        self.key = "ai_state_basic"
        self.desc = "Performs basic AI actions, such as ranged and melee attacks, patrolling, and respawning"
        self.interval = 3  # Shield regen ticks every second
        self.persistent = True  # Will survive reload

        # If this script is on a PlayerCharacter, it will be removed on start
        if utils.inherits_from(self.obj, 'typeclasses.characters.PlayerCharacter'):
            self.obj.scripts.delete(self)

    def at_start(self):
        self.msged = False

    def at_repeat(self):
        
        if self.obj.ndb.target

        