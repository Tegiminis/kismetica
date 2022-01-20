
class InventoryHandler(object):
    obj = None

    def __init__(self, obj) -> None:
        self.obj = obj
        if not self.obj.attributes.has('weapons'): self.obj.db.weapons = {'primary': None, 'special': None, 'power': None}
        if not self.obj.attributes.has('armor'): self.obj.db.armor = {'head': None, 'gloves': None, 'chest': None, 'legs': None, }
    
    @property
    def weapons(self):
        return self.obj.db.weapons
    
    @property
    def armor(self):
        return self.obj.db.armor