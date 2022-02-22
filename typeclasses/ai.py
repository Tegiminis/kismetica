from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typeclasses.npc import NPC

class AIHandler():
    
    obj = None

    def __init__(self, obj):
        self.obj = obj

    def change_state(self, state:str):
        pass