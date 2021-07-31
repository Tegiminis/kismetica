from typing import List
from .objects import Object
import time
from .bufflist import BuffList as buffs
import world.destiny_rules as dr
import random

def add_buff(handler: dict, buff: str, stacks: int = 1):
    '''Add a buff to an object or player that can have buffs.
    
    Args:
        handler: The handler you wish to add the buff to (any dict works)
        buff: A string matching the variable name of the buff in bufflist.py
        stacks: The number of stacks you want to add, if the buff is stacking (optional; defaults to 1)
    '''

    b = vars(buffs).get(buff)       # Copy an instance of the buff to a dict
    b['time'] = time.time()         # Set the instance's start time
    id = b['id']                    # Get the id of the buff

    # Three types of buff: stacking, unique, and instanced.
    # Stacking buffs always find an existing buff and add more stacks to it.
    # Unique buffs do not stack and refresh entirely on reapplication
    if b['stacking'] == True:
        add_stacks(handler, b, stacks)
    elif b['refresh'] == True:
        handler[id] = b
    else:
        uid = str( int( random.random() * 10000 ))
        handler[ id + uid ] = b
    
def remove_buff(handler:dict, buffid: str):
    '''Remove a buff with matching buffid from the specified handler.'''
    del handler[buffid]

def add_stacks(handler: dict, buff: dict, stacks: int):
    '''Adds the number of stacks to an existing buff on the handler, or adds a new instance if none exists.'''
    id = buff.get('id')
    refresh = buff.get('refresh')
    if handler.get(id): 
        if refresh: handler[id]['time'] = time.time()
        handler[id]['stacks'] = min( handler[id]['stacks'] + stacks, handler[id]['maxstacks'] ) 
    else: handler[id] = buff

def check_buffs(obj: Object, base: float, stat: str) -> float:    
    '''Finds all buffs related to a stat and applies their effects.
    
    Args:
        obj: The object with a buffhandler
        base: The base value you intend to modify
        stat: The string that designates which stat buffs you want
        
    Returns the base value, modified by the relevant buffs'''

    # Buff handler assignment, so we can find the relevant buffs
    bh = None
    bh: dict = obj.db.buffhandler
    if bh == None:
        return base

    # Do the first bit of buff cleanup
    buff_cleanup(bh)

    if len(bh.keys()) <= 0:
        return base

    # Find all buffs related to the specified stat.
    stat_dict = find_buffs_by_value(bh, 'stat', stat)

    # Add all arithmetic buffs together
    add_dict = find_buffs_by_value(stat_dict, 'mod', 'add')
    add = calc_buff(add_dict)

    # Add all multiplication buffs together
    mult_dict = find_buffs_by_value(stat_dict, 'mod', 'mult')
    mult = calc_buff(mult_dict)

    # The final result
    final = (base + add) * (1 + mult)

    return final

def find_buffs_by_value(handler, key: str, val) -> dict:
    '''Helper function that does dictionary comprehension to find all entries which have a key entry that matches the value within a nested dict.'''
    dict = { k:v for k,v in handler.items() if v.get(key) == val }
    return dict

def calc_buff(buffs: dict):
    '''Given a dictionary of buffs, add all the values together.'''
    x = 0.0
    for k,v in buffs.items():
        b = v.get('base')
        s = v.get('stacks')
        ps = v.get('perstack')

        x += b + ((1 - s) * ps)
    return x

def buff_cleanup(handler: dict):
    '''Checks all buffs on the dictionary, and cleans up old ones.'''
    remove = [ k 
        for k,v in handler.items() 
        if dr.check_time(v.get('time'), time.time(), v.get('duration')) ]
    for k in remove: del handler[k]