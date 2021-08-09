from typeclasses.buff import Buff, Mod
from typeclasses.perk import Effect
from typing import List

from evennia import DefaultObject
from typeclasses.objects import Object
import time
import typeclasses.content.bufflist as bl
import world.rules as dr
import random

def add_buff(obj: DefaultObject, buff: str, stacks = 1, duration = None) -> str:
    '''Add a buff instance to an object or player that can have buffs, respecting all stacking/refresh/reapply rules.
    
    Args:
        obj: The object you wish to add the buff to (requires "buffs" database variable)
        buff: A string matching the variable name of the buff in bufflist.py
        stacks: (optional; defaults to 1) The number of stacks you want to add, if the buff is stacking
        duration: (optional; defaults to template buff duration) The amount of time, in seconds, you want the buff to last.
    
    Returns the key string for the buff instance that was added.
    '''

    cleanup_buffs(obj)

    _ref = vars(bl.BuffList).get(buff)     # The type reference to our buff
    id = _ref.id

    b = { 'ref': _ref, 'start': time.time(), 'stacks': stacks }     # Create the buff instance that holds the type reference, start time, and stacks

    # Set the instance's duration. Either the buff's default duration, or one you specify
    if duration is not None: b['duration'] = duration
    else: b['duration'] = _ref.duration

    r_id = apply_buff(obj, id, b, stacks)
    return r_id

def apply_buff(obj: DefaultObject, id: str, buff: dict, stacks) -> str:
    '''Apply a buff to an object, accessible by id. Returns the handler key of the applied buff.'''
    handler: dict = None
    br = buff.get('ref')()

    if isinstance(br, Effect): handler = obj.db.effects
    elif isinstance(br, Buff): handler = obj.db.buffs

    p_id = id
    uid = str( int( random.random() * 10000 ))

    if id in handler.keys():
        if br.unique:
            return None
        elif br.stacking:
            if br.refresh: 
                handler[id]['start'] = time.time()
            handler[id]['stacks'] = min( handler[id]['stacks'] + stacks, br.maxstacks )
            br.on_apply(obj)
        elif br.refresh:
            handler[id] = buff
            br.on_apply(obj)
        elif br.unique is False: 
            p_id = id + uid
            handler[p_id] = buff
            br.on_apply(obj)
    else: 
        handler[id] = buff
        br.on_apply(obj)
    
    return p_id

def remove_buff(obj: DefaultObject, id: str):
    '''Remove a buff with matching id from the specified object. Calls the buff's on_remove function.'''
    handler = obj.db.buffs
    buff: Buff = handler[id].get('ref')()
    buff.on_remove(obj)
    del handler[id]

def cleanup_buffs(obj):
    '''Checks all buffs on the object, and cleans up old ones.'''
    handler = obj.db.buffs
    if handler:
        remove = [ k 
            for k,v in handler.items() 
            if time.time() - v.get('start') > v.get('duration') ]
        for k in remove: remove_buff(obj, k)

def view_buffs(obj) -> list:
    '''Gets the name and flavor of all buffs on the object.'''
    cleanup_buffs(obj)
    handler = obj.db.buffs
    message = []

    for x in handler.values():
        buff: Buff = x.get('ref')()
        msg = buff.name + ": " + buff.flavor
        message.append(msg)
    
    return message

def find_buffs_by_value(handler: list, key: str, value) -> dict:
    '''Returns a list of all buffs on the handler with a mod whose variable matches the value.'''
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