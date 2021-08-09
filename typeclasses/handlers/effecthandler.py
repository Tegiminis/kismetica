from typeclasses.objects import Object
from typeclasses.perk import Effect
import time

def trigger_effect(context, trigger: str):
    '''Activates all effects on the obj that have the same trigger string.'''
    
    cleanup_effects(context)

    activate = []
    for x in context.db.effects.values():
        instance = x.get('ref')()
        if instance.trigger == trigger:
            activate.append(instance)
    if activate is None: return
    for x in activate: x.on_trigger(context)
    activate = None

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