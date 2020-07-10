from typeclasses.characters import Character

# destiny_rules is the rules module that contains all combat calculations, enums, and other important doodads
from world import destiny_rules

class NPC(Character):
    def at_object_creation(self):
        super().at_object_creation()
        
        # Death messaging. Defaults to a generic death.
        self.db.msg_death = "The %s crumples to the ground, dead." % str(self.name)

        # If an NPC is dead, it can be looted and cannot perform any actions
        self.db.npc_dead = False

        # If any NPC is active, it is visible by players
        self.db.npc_active = True
