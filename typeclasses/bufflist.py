from typeclasses.buff import BaseBuff
from typeclasses.buff import Mod  
    
class RampageBuff(BaseBuff):
    id = 'rampage'
    name = 'Rampage'
    flavor = 'Defeating an enemy has filled you with bloodlust.'

    duration = 30

    refresh = True
    stacking = True
    unique = False
    maxstacks = 3

    mods = [ Mod('damage', 'mult', 9, 10), Mod('damage', 'add', 90, 10) ]

    def on_remove(self, context):
        context.msg('The bloodlust fades.')