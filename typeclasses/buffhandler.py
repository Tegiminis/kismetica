from typeclasses.buff import BaseBuff
from typeclasses.buff import Mod
from typing import List

from evennia import DefaultObject
from .objects import Object
import time
import typeclasses.bufflist as bl
import world.destiny_rules as dr
import random

class BuffList():
    '''Initialization of buff typeclasses used to apply buffs to players.

    If it's not in this list, it won't be usable in-game without python access.'''
    rampage = bl.RampageBuff

def check_buffs(obj: Object, base: float, stat: str) -> float:    
    '''Finds all buffs related to a stat and applies their effects.
    
    Args:
        obj: The object with a buffhandler
        base: The base value you intend to modify
        stat: The string that designates which stat buffs you want
        
    Returns the base value, modified by the relevant buffs'''

    # Do the first bit of buff cleanup
    buff_cleanup(obj)

    # Buff handler assignment, so we can find the relevant buffs
    handler = []
    if obj.db.buffs: handler = obj.db.buffs.values()
    else: return base

    # Find all buffs related to the specified stat.
    stat_list = find_buffs_by_value(handler, 'stat', stat)
    if stat_list is None: return base

    # Add all arithmetic buffs together
    add_list = find_buffs_by_value(stat_list, 'modifier', 'add')
    obj.msg(str(add_list))
    add = apply_mods(add_list, "add")
    obj.msg("Additional damage: " + str(add))

    # Add all multiplication buffs together
    mult_list = find_buffs_by_value(stat_list, 'modifier', 'mult')
    mult = apply_mods(mult_list, "mult")
    obj.msg("Damage multiplier: " + str(1 + mult))

    # The final result
    final = (base + add) * (1 + mult)

    return final

def find_buffs_by_value(handler: list, key: str, value) -> dict:
    '''Returns a list of all buffs on the handler with a mod whose variable matches the value.'''
    if handler is None: return None
    
    b = []

    for v in handler:
        buff: BaseBuff = v.get('ref')()
        for _m in buff.mods:
            _m: Mod
            val = vars(_m).get(key)
            if value == val: 
                b.append(v)
                break

    return b

def apply_mods(buffs: list, modifier):
    '''Given a list of buffs, add all the values together.'''
    x = 0.0
    if buffs is None: return x
    
    for v in buffs:
        buff: BaseBuff = v.get('ref')()
        for _m in buff.mods:
            _m : Mod
            if _m.modifier == modifier:
                b = _m.base
                s = v.get('stacks')
                ps = _m.perstack

                x += b + ( (s - 1) * ps )
    return x

def add_buff(obj: DefaultObject, buff: str, stacks = 1, duration = None) -> str:
    '''Add a buff to an object or player that can have buffs.
    
    Args:
        obj: The object you wish to add the buff to (requires "buffs" database variable)
        buff: A string matching the variable name of the buff in bufflist.py
        stacks: The number of stacks you want to add, if the buff is stacking (optional; defaults to 1)
        duration: The amount of time, in seconds, you want the buff to last. Uses buff duration if not set
    '''

    buff_cleanup(obj)

    _ref = vars(BuffList).get(buff)     # The type reference to our buff
    id = _ref.id
    obj.msg("Buff ID to add: " + id)

    b = { 'ref': _ref, 'start': time.time(), 'stacks': stacks }     # Create the buff instance that holds the type reference, start time, and stacks

    # Set the instance's duration. Either the buff's default duration, or one you specify
    if duration is not None: b['duration'] = duration
    else: b['duration'] = _ref.duration

    r_id = apply_buff(obj, id, b, stacks)
    return r_id

def apply_buff(obj: DefaultObject, id: str, buff: dict, stacks) -> str:
    '''Apply a buff to an object, accessible by id. Returns a reference to the applied buff.'''
    handler: dict = obj.db.buffs
    br: BaseBuff = buff.get('ref')()
    uid = str( int( random.random() * 10000 ))

    if id in handler.keys():
        if br.stacking:
            if br.refresh: 
                handler[id]['start'] = time.time()
            handler[id]['stacks'] = min( handler[id]['stacks'] + stacks, br.maxstacks )
            br.on_apply(obj)
        elif br.refresh:
            handler[id] = buff
            br.on_apply(obj)
        elif br.unique is False: 
            handler[ id + uid ] = buff
            br.on_apply(obj)
        else: return
    else: 
        handler[id] = buff
        br.on_apply(obj)
    
    return id

def remove_buff(obj: DefaultObject, id: str):
    '''Remove a buff with matching id from the specified object. Calls the buff's on_remove function.'''
    handler = obj.db.buffs
    buff: BaseBuff = handler[id].get('ref')()
    buff.on_remove(obj)
    del handler[id]

def buff_cleanup(obj):
    '''Checks all buffs on the object, and cleans up old ones.'''
    handler = obj.db.buffs
    if handler:
        remove = [ k 
            for k,v in handler.items() 
            if time.time() - v.get('start') > v.get('duration') ]
        for k in remove: remove_buff(obj, k)

def view_buffs(obj) -> list:
    '''Gets the name and flavor of all buffs on the object.'''
    buff_cleanup(obj)
    handler = obj.db.buffs
    message = []

    for x in handler.values():
        buff: BaseBuff = x.get('ref')()
        msg = buff.name + ": " + buff.flavor
        message.append(msg)
    
    return message