from typeclasses.objects import Object


class Item(Object):
    def at_before_get(self, getter, **kwargs):
        return super().at_before_get(getter, **kwargs)

    def at_get(self, getter, **kwargs):
        return super().at_get(getter, **kwargs)

    def at_object_creation(self):
        self.db.weight = 1
        self.db.stacking = False


class InventoryHandler(object):
    obj = None

    def __init__(self, obj) -> None:
        self.obj = obj
        if not self.obj.attributes.has("weapons"):
            self.obj.db.weapons = {"kinetic": None, "energy": None, "power": None}
        if not self.obj.attributes.has("armor"):
            self.obj.db.armor = {
                "head": None,
                "gloves": None,
                "chest": None,
                "legs": None,
            }

    @property
    def weapons(self):
        return

    @property
    def armor(self):
        return

    @property
    def equipped(self):
        return

    @property
    def encumberance(self):
        """The character's current encumberance; added weight of all items carried."""
        _weight = 0

        for x in self.obj.contents:
            if x.is_typeclass(Item):
                if x not in self.armor and x not in self.weapons:
                    _weight += x.db.weight

        return _weight

    @property
    def bulk(self):
        """The character's current "bulk"; that is, the total size of the items they carry"""
        return
