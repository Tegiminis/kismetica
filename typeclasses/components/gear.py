
class GearHandler(object):
    obj = None

    def __init__(self, obj) -> None:
        self.obj = obj
        if not self.obj.has('weapons'): self.obj.db.weapons = []
        if not self.obj.has('armor'): self.obj.db.armor = {}
    
    @property 
    def weapons(self):
        return self.obj.db.weapons

    @property 
    def armor(self):
        return self.obj.db.armor

    def equip():
        pass