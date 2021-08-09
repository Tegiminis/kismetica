from typeclasses.context import BuffContext, Context, generate_context
import typeclasses.handlers.perkhandler as ph
from typeclasses.buff import BaseBuff, Buff, Mod
from typeclasses.perk import Effect
from typing import List

from evennia import DefaultObject
from typeclasses.objects import Object
import time
import typeclasses.content.bufflist as bl
import world.rules as dr
import random
from evennia import utils

def add_buff(origin: DefaultObject, target: DefaultObject, buff: str, stacks = 1, duration = None) -> Context:
    '''Add a buff or effect instance to an object or player that can have buffs, respecting all stacking/refresh/reapply rules.
    
    Args:
        obj: The object you wish to add the buff to (requires "buffs" database variable)
        buff: A string matching the variable name of the buff in bufflist.py
        stacks: (optional; defaults to 1) The number of stacks you want to add, if the buff is stacking
        duration: (optional; defaults to template buff duration) The amount of time, in seconds, you want the buff to last.
    
    Returns the buff context for the action.
    '''

    cleanup_buffs(target)

    # The type reference to our buff
    _ref = vars(bl.BuffList).get(buff)     
    id = _ref.id

    # Create the buff dict that holds the type reference, start time, and stacks
    b = { 'ref': _ref, 'start': time.time(), 'stacks': stacks }     

    # Set the instance's duration. Either the buff's default duration, or one you specify
    if duration is not None: b['duration'] = duration
    else: b['duration'] = _ref.duration

    # Clean up the buff at the end of its duration through a delayed cleanup call
    utils.delay( b['duration'] + 0.01, cleanup_buffs, target, persistent=True )

    # Apply the buff and pass the BuffContext upwards.
    context = apply_buff(origin, target, id, b, stacks)

    return context

def apply_buff(origin: DefaultObject, target: DefaultObject, id: str, buff: dict, stacks):
    '''Apply a buff to an object, accessible by id. Returns the handler key of the applied buff.'''
    handler: dict = None
    br = buff.get('ref')()

    if isinstance(br, Effect): handler = target.db.effects
    elif isinstance(br, Buff): handler = target.db.buffs

    p_id = id
    uid = str( int( random.random() * 10000 ))

    if id in handler.keys():
        if br.unique:
            return None
        elif br.stacking:
            if br.refresh: 
                handler[id]['start'] = time.time()
            handler[id]['stacks'] = min( handler[id]['stacks'] + stacks, br.maxstacks )
        elif br.refresh:
            handler[id] = buff
        elif br.unique is False: 
            p_id = id + uid
            handler[p_id] = buff
    else: 
        handler[id] = buff
    
    context: BuffContext = generate_context(origin, target, handler=handler, buff=p_id)

    return context

def remove_buff(origin: DefaultObject, target: DefaultObject, id: str, dispel=False, expire=False, kill=False):
    '''Remove a buff with matching id from the specified object. Calls on_remove, on_dispel, or on_expire, depending on arguments.
    
    Args:
        obj:    Object to remove buff from
        id:     The buff id
        dispel: Call on_dispel when True.
        expire: Call on_expire when True.
        kill:   Do not call on_remove when True.'''
    handler = None
    
    if id in target.db.buffs.keys(): handler = target.db.buffs
    elif id in target.db.effects.keys(): handler = target.db.effects
    else: return None

    buff: Buff = handler[id].get('ref')()
    context = generate_context(origin, target, buff=id, handler=handler)

    if dispel: buff.on_dispel(context)
    elif expire: buff.on_expire(context)
    elif not kill: buff.on_remove(context)

    del handler[id]
    
    return generate_context(actor=origin, actee=target, buff=id, handler=handler)

def cleanup_buffs(obj) -> str:
    '''Checks all buffs and effects on the object, and cleans up old ones. Returns all cleanup messages.'''
    def cleanup(handler):
        if handler:
            remove = [ k 
                for k,v in handler.items() 
                if time.time() - v.get('start') > v.get('duration') ]
            for k in remove: 
                remove_buff(obj, obj, k, expire=True)

    handler = obj.db.buffs
    cleanup(handler)

    handler = obj.db.effects
    cleanup(handler)

    return
 

def view_buffs(obj) -> list:
    '''Gets the name and flavor of all buffs and effects on the object.'''
    cleanup_buffs(obj)
    message = []
    
    if obj.db.buffs:
        handler = obj.db.buffs.values()
        for x in handler:
            buff: Buff = x.get('ref')()
            msg = buff.name + ": " + buff.flavor
            message.append(msg)

    if obj.db.effects: 
        handler = obj.db.effects.values()
        for x in handler:
            buff: Buff = x.get('ref')()
            msg = buff.name + ": " + buff.flavor
            message.append(msg)
    
    return message

def find_mods_by_value(handler: list, key: str, value) -> dict:
    '''Returns a list of all buffs and traits on the handler with a mod whose variable matches the value.'''
    if handler is None: return None
    
    b = []

    for v in handler:
        buff: Buff = v.get('ref')()
        if buff.mods:
            for _m in buff.mods:
                _m: Mod
                val = vars(_m).get(key)
                if value == val: 
                    b.append(v)
                    break

    return b

def calculate_mods(buffs: list, modifier):
    '''Given a list of buffs, add all the values together.'''
    x = 0.0
    if buffs is None: return x
    
    for v in buffs:
        buff: Buff = v.get('ref')()
        for mod in buff.mods:
            mod : Mod
            if mod.modifier == modifier:
                b = mod.base
                s = v.get('stacks')
                ps = mod.perstack

                x += b + ( (s - 1) * ps )
    return x