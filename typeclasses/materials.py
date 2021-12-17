from objects import Object

class Material(Object):
    '''Stacking objects used for crafting and trading.'''

    def at_object_creation(self):
        super().at_object_creation()

        self.db.stacks = 1

    pass