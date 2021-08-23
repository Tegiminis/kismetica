from typeclasses.subclass import Subclass
from typeclasses.buff import Trait, Mod

class SoldierMarksman(Trait):
    id = 'soldiermarksman'
    name = 'Marksman'
    flavor = 'Increased accuracy.'

    mods = [
        Mod('accuracy', 'add', 2.0)
    ]

class Soldier(Subclass):
    '''The most basic subclass. Gives you access to realistic (read: non-magic) abilities.'''
    id = 'soldier'

    levelCap = 5

    traits = {
        1: SoldierMarksman,
        2: None,
        3: None,
        4: None,
        5: None
    }