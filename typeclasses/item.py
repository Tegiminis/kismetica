from typeclasses.objects import Object

class Item(Object):
    
    def at_object_creation(self):
        self.db.weight = 1          # Object's weight. If this would put you over the max weight, you can't pick it up
        self.db.stacking = False