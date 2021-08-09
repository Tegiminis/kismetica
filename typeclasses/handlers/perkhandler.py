from typeclasses.buff import Trait
from typeclasses.perk import Perk
import typeclasses.content.perklist as pl

def add_perk(obj, ref):
    '''Adds the referenced perk or trait to the object's relevant handler. Must match variable name in PerkList exactly.'''
    p = vars(pl.PerkList).get(ref)
    id = p.id
    slot = p.slot

    if isinstance(p, Perk): obj.db.perks[slot] = p
    elif isinstance(p, Trait): obj.db.traits[id] = p

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