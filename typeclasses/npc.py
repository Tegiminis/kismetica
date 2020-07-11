from typeclasses.characters import Character

# destiny_rules is the rules module that contains all combat calculations, enums, and other important doodads
from world import destiny_rules

class NPC(Character):
    
    def at_object_creation(self):
        super().at_object_creation()
        
        # Death messaging. Defaults to a generic death.
        self.db.msg = {
            'despawn': "%s crumbles away into a fine dust." % self.named(),
            'advance': "%s lumbers forward, stomped the ground with chitinous feet." % self.named(),
            'retreat': "%s backs up to find a better position." % self.named()
        }

        self.db.lootable = True

        # Various AI timers and things
        self.db.timer = {
            'idle': 3,     # How long after idling before thinking again
            'attack': 1,   # How long after attacking before thinking again
            'patrol': 3,   # How long after patrolling before thinking again
            'respawn': 30,  # How long until this AI despawns and respawns at home
            'active': 10   # How long after respawn before thinking again
        }

        self.db.ideal_range = 30    # Range, in room_depth, that the AI will try to reach before shooting

        # States for the state machine
        self.db.state = {
            'dead': False,          # Is this NPC dead? Dead NPCs show their 'dead' room message, and eventually return to spawn
            'active': True,         # Is this NPC active? Active NPCs do things; inactive NPCs are invisible to the player
            'aggressive': False,    # Is this NPC aggressive? Aggressive NPCs attack the player on sight
            'patrolling': False,    # Is this NPC patrolling? Patrolling NPCs move from room to room
            'attacking': False      # Is this NPC attacking? Attacking NPCs perform their combat actions
        }
