from typeclasses.perk import BasePerk as Perk
import typeclasses.perklist as pl
from typeclasses.objects import DefaultObject as Object

class PerkList():
    rampage = pl.RampagePerk

def add_perk(context, ref):
    '''Adds the referenced perk to the context's perkhandler. Must match variable name in PerkList (above) exactly.'''
    p = vars(PerkList).get(ref)
    id = p.id
    slot = p.slot

    if slot: context.db.perks[slot] = p
    else: context.db.perks[id] = p

def trigger_perk(context, trigger: str):
    '''Activates all perks on the obj that have the same trigger string.'''
    activate = []
    for x in context.db.perks.values():
        instance = x()
        if instance.trigger == trigger:
            activate.append(instance)
    if activate is None: return
    for x in activate: x.on_trigger(context)
    activate = None