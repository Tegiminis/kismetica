import random
import time
from typeclasses.scripts import Script
from typeclasses.npc import NPC
from evennia import utils
from world import destiny_rules as rules

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
        self.start_delay = True

        self.tags.add( 'ai' )

        # If this script is on anything but an NPC, it will be removed on start
        if utils.inherits_from(self.obj, 'typeclasses.self.obj.NPC') is False:
            self.obj.scripts.delete(self)

    def at_start(self):
        pass

    def at_repeat(self):

        state = self.obj.db.state
        delay = 5       

        # If this AI is "attacking", it does the basic AI ranged attack
        if state == 'attack':           
            if self.obj.db.target == None:
                self.obj.db.state = 'search'
            if self.obj.db.target != None:                               # If NPC has a target      
                if self.obj.db.target.location == self.obj.location:              # If the target is in the same location as the NPC
                    delay = self.obj.db.basic_ranged['cooldown']
                    self.obj.npc_attack(self.obj.db.target)                    
                elif self.obj.db.target.location != self.obj.location:       # If the target is not in the same location
                    self.obj.db.target = None                         
                    self.obj.db.state = 'search'                         # Couldn't find any targets? Search for easy pickings.

        # If this AI is searching the current room, it tries to find a target to attack
        if state == 'search':
            delay = self.obj.db.timer['search']
            
            targets = self.obj.find_targets(self.obj.location)
            if targets:
                self.obj.db.target = random.choice(targets)

            # If you found a target, start attacking.
            # Otherwise, if the dice roll right, go on patrol.
            target = self.obj.db.target
            if target != None:
                delay = self.obj.db.timer['attack']
                self.obj.db.state = 'attack'   
            else:
                self.obj.location.msg_contents( random.choice(self.obj.db.msg['idle']).capitalize() )
                self.obj.db.state = 'patrol'

        # If the AI is patrolling, that means it is randomly moving from room to room in search of targets
        if state == 'patrol':
            self.obj.patrol_move()
            delay = self.obj.db.timer['search']
            self.obj.db.state = 'search'       
        
        # If this AI is ready to respawn, teleport it home and make it start patrolling
        if state == 'respawn':
            rules.revive(npc)
            delay = self.obj.db.timer['patrol']
            self.obj.db.state = 'patrol'
        
        # If this AI is dead, begin respawn process
        if state == 'dead':
            self.obj.location.msg_contents( self.obj.db.msg['despawn'].capitalize() )
            self.obj.move_to(self.obj.home, True)
            delay = self.obj.db.timer['respawn']
            self.obj.db.state = 'respawn'

        self.restart( interval=delay )


        
        



        