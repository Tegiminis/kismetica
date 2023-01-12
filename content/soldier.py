from evennia.contrib.rpg.buffs.buff import BaseBuff, Mod


class SoldierMarksman(BaseBuff):
    id = "soldiermarksman"
    name = "Marksman"
    flavor = "Increased accuracy."

    mods = [Mod("accuracy", "add", 2.0)]


class Soldier:
    """The most basic subclass. Gives you access to realistic (read: non-magic) abilities."""

    id = "soldier"

    levelCap = 5

    traits = {1: SoldierMarksman, 2: None, 3: None, 4: None, 5: None}
