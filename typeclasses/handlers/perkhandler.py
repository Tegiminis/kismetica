import typeclasses.handlers.buffhandler as bh
from typeclasses.objects import Object
import typeclasses.content.perklist as pl
from typeclasses.buff import BaseBuff, Buff, Perk, Trait, Effect, Mod
from typeclasses.context import generate_context
from evennia import utils
import time

def add_perk(obj: Object, perk, slot: str = None):
    '''Adds the referenced perk or trait to the object's relevant handler. Must match variable name in PerkList exactly.'''
    id = perk.id
    slot = perk.slot

    if utils.inherits_from(perk, Perk):
        if slot: obj.db.perks[slot] = perk
        else: obj.db.perks[id] = perk
    if utils.inherits_from(perk, Trait):
        if slot: obj.db.traits[slot] = perk
        else: obj.db.traits[id] = perk
        

def remove_perk(origin, target, id):
    '''Removes a perk or trait with matching id from the object's handler. Calls the perk's on_remove function.'''
    handler = None
    
    if id in target.db.perks.keys(): handler = target.db.perks
    elif id in target.db.traits.keys(): handler = target.db.traits
    else: return None

    perk: Perk = handler.get(id)()
    context = generate_context(target, origin, perk=id, handler=handler)

    perk.on_remove(context)

    del handler[id]
    return context

def trigger_effects(target, trigger: str, origin=None) -> str:
    '''Activates all perks and effects on the obj that have the same trigger string. Returns a list of all messaging for the perks/effects'''
    bh.cleanup_buffs(target)
    if not origin: origin = target
    
    perks_activate = []
    effects_activate = []
    messaging = []     

    # Find all perks to trigger
    perks = target.db.perks
    for y in perks.values():
            instance = y()
            if instance.trigger == trigger:
                perks_activate.append(instance)

    # Find all effects to trigger (has to be separate because of how the dicts work)
    effects = target.db.effects
    for y in effects.values():
            instance = y.get('ref')()
            if instance.trigger == trigger:
                effects_activate.append(instance)
    
    # Go through and trigger all relevant perks and effects, passing their trigger messages upwards.
    for x in perks_activate:
        x : Perk
        handler = perks
        context = generate_context(target, origin)
        trigger_context = x.on_trigger(context)
    for x in effects_activate:
        x : Effect
        handler = effects
        context = generate_context(target, origin, buff=x.id, handler=handler)
        trigger_context = x.on_trigger(context)
    
    _msg = ''
    for x in messaging: _msg += x + "\n|n"
    return _msg