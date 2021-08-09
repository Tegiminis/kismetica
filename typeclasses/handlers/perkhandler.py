from typeclasses.context import generate_context
from typeclasses.buff import Trait
import typeclasses.handlers.buffhandler as bh
from typeclasses.perk import Effect, Perk
from typeclasses.objects import Object
import typeclasses.content.perklist as pl
import time

def add_perk(obj, ref):
    '''Adds the referenced perk or trait to the object's relevant handler. Must match variable name in PerkList exactly.'''
    p = vars(pl.PerkList).get(ref)
    id = p.id
    slot = p.slot

    obj.db.perks[slot] = p
    if isinstance(p, Trait): obj.db.traits[id] = p

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

    # Find all effects to trigger
    effects = target.db.effects
    for y in effects.values():
            instance = y.get('ref')()
            if instance.trigger == trigger:
                effects_activate.append(instance)
    
    # Go through all the perks and effects, and trigger all of them, passing their trigger messages upwards.
    for x in perks_activate:
        x : Perk
        handler = perks
        context = generate_context(actee=target, actor=origin)
        trigger_context = x.on_trigger(context)
    for x in effects_activate:
        x : Effect
        handler = effects
        context = generate_context(actee=target, actor=origin, buff=x.id, handler=handler)
        trigger_context = x.on_trigger(context)
    
    _msg = ''
    for x in messaging: _msg += x + "\n|n"
    return _msg

def cleanup_effects(obj):
    '''Checks all effects on the object, and cleans up old ones.'''
    handler = obj.db.effects
    if handler:
        remove = [ k 
            for k,v in handler.items() 
            if time.time() - v.get('start') > v.get('duration') ]
        for k in remove: remove_effect(obj, k)

def remove_effect(obj: Object, id: str):
    '''Remove an effect with matching id from the specified object. Calls the effect's on_remove function.'''
    handler = obj.db.effects
    eff: Effect = handler[id].get('ref')()
    eff.on_remove(obj)
    del handler[id]