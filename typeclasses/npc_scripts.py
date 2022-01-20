import random
import time
from typeclasses.scripts import Script
from typeclasses.npc import NPC
from evennia import utils

class AIBasic(Script): 
    """
    A script which acts as a basic state machine for any non-puppeted character it is attached to.

    This script is actively placed on all NPCs at init.
    Default AI actions include attacking with ranged and melee weapons, and patrolling
    This state machine also handles the AI dying and reviving, among other things.
    """
    def at_script_creation(self):
        self.key = "ai_basic"
        self.desc = "Performs basic AI actions, such as ranged and melee attacks, patrolling, and respawning"
        self.interval = 1
        self.start_delay = True
        self.persistent = True

        self.tags.add( 'ai' )

        # If this script is on anything but an NPC, it will be removed on start
        if utils.inherits_from(self.obj, 'typeclasses.npc.NPC') is False:
            self.obj.scripts.delete(self)

    def at_start(self):
        pass

    def at_repeat(self):

        npc : NPC = self.obj
        
        state = npc.db.state
        delay = 5  

        # If this AI is "attacking", it does the basic AI ranged attack
        if state == 'attack':           
            if npc.db.target.is_superuser: npc.db.target = None
            
            if npc.db.target != None:                                     
                if npc.db.target.location == npc.location:              
                    delay = npc.db.basic_ranged['cooldown']
                    npc.npc_attack(npc.db.target)                    
                elif npc.db.target.location != npc.location:       
                    hunt = npc.hunt(npc.db.target)
                    if hunt != None: npc.move_to(hunt)
                    else: npc.db.target = None                         

            if npc.db.target == None: npc.db.state = 'search'

        # If this AI is searching the current room, it tries to find a target to attack
        if state == 'search':
            delay = npc.db.timer['search']
            
            targets = npc.find_targets(npc.location)
            if targets:
                npc.db.target = random.choice(targets)

            # If you found a target, start attacking.
            # Otherwise, if the dice roll right, go on patrol.
            target = npc.db.target
            if target != None:
                delay = npc.db.timer['attack']
                npc.db.state = 'attack'   
            else:
                npc.location.msg_contents( random.choice(npc.db.msg['idle']).capitalize() )
                npc.db.state = 'patrol'

        # If the AI is patrolling, that means it is randomly moving from room to room in search of targets
        if state == 'patrol' or state == 'active':
            npc.patrol_move()
            delay = npc.db.timer['search']
            npc.db.state = 'search'       
        
        # If this AI is ready to respawn, teleport it home and make it start patrolling
        if state == 'respawn':
            npc.db.health['current'] = npc.db.health['max']
            npc.db.shield['current'] = npc.db.shield['max']
            npc.location.msg_contents( npc.db.msg['respawn'].capitalize() )
            delay = npc.db.timer['patrol']
            npc.db.state = 'patrol'
        
        # If this AI is dead, begin respawn process
        if state == 'dead':
            npc.location.msg_contents( npc.db.msg['despawn'].capitalize() )
            npc.move_to(npc.home, True)
            delay = npc.db.timer['respawn']
            npc.db.state = 'respawn'

        self.restart( interval=delay )    