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
        self.interval = 1
        self.persistent = True  # Will survive reload

        self.db.lt = 0      # When this script last fired
        self.db.delay = 3

        # If this script is on a PlayerCharacter, it will be removed on start
        if utils.inherits_from(self.obj, 'typeclasses.characters.PlayerCharacter'):
            self.obj.scripts.delete(self)

    def at_start(self):
        now = time.time()
        self.db.lt = now

    def at_repeat(self):
        
        now = time.time()
        ai = self.obj

        if now - self.db.lt > delay:

            if ai.db.state['dead'] is True:
                ai.move_to(ai.home, True)
                delay = ai.db.timer['active']
                self.db.lt = now

        
        



        