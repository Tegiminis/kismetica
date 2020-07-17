from typeclasses.characters import Character

# destiny_rules is the rules module that contains all combat calculations, enums, and other important doodads
from world import destiny_rules

class NPC(Character):
    
    def at_object_creation(self):
        super().at_object_creation()
        
        # Various types of messaging
        self.db.msg = {
            'despawn': "%s crumbles away into a fine dust." % self.named(),
            'advance': "%s lumbers forward, stomping the ground with chitinous feet." % self.named(),
            'retreat': "%s backs up to find a better position." % self.named()
        }

        self.db.lootable = True     # Can this mob be looted?

        # Various AI timers and things
        self.db.timer = {
            'idle': 3,              # How long after idling before thinking again
            'attack': 3,            # How long after attacking before thinking again
            'patrol': 3,            # How long after patrolling before thinking again
            'dead': 30,             # How long this AI remains dead before it respawns
            'respawn': 10           # How long after respawn before thinking again
        }

        self.db.ideal_range = 30    # Range, in room_depth, that the AI will try to reach before shooting

        # States for the state machine
        self.db.state = 'active'
