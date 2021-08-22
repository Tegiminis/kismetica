from typeclasses.objects import Object

class Item(Object):
    
    def at_object_creation(self):
        return super().at_object_creation()
    pass