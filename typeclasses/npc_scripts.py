import random
import time
from typeclasses.scripts import Script
from evennia import utils
import destiny_rules as rules

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
        self.persistent = True      # Will survive reload
        self.start_delay = True

        self.tags.add( 'ai' )

        # If this script is on a PlayerCharacter, it will be removed on start
        if utils.inherits_from(self.obj, 'typeclasses.characters.PlayerCharacter'):
            self.obj.scripts.delete(self)

    def at_start(self):
        pass

    def at_repeat(self):
        
        ai = self.obj
        delay = 1        

        if ai.db.state is 'patrol':
            pass
        
        # If this AI is "active", do the various checks to put it into different states
        if ai.db.state is 'active':
            pass
        
        # If this AI is ready to respawn, teleport it home and make it active again
        if ai.db.state is 'respawn':
            rules.revive(ai)
            delay = ai.db.timer['active']
            ai.db.state = 'active'
        
        # If this AI is dead, begin respawn process
        if ai.db.state is 'dead':
            ai.location.msg_contents( ai.db.msg['despawn'].capitalize() )
            ai.move_to(ai.home, True)
            delay = ai.db.timer['respawn']
            ai.db.state = 'respawn'

        self.restart( interval=delay )


        
        



        