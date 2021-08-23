import time
import random

import typeclasses.handlers.perkhandler as ph
from typeclasses.buff import BaseBuff, Buff, Perk, Trait, Effect, Mod
from typeclasses.objects import Object
from evennia import utils
from typeclasses.context import BuffContext, Context, generate_context

def add_buff(origin: Object, target: Object, buff: BaseBuff, stacks = 1, duration = None) -> Context:
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
    _ref = buff  
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

def apply_buff(origin: Object, target: Object, id: str, buff: dict, stacks):
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

def remove_buff(origin: Object, target: Object, id: str, dispel=False, expire=False, quiet=False, delay=0):
    '''Remove a buff or effect with matching id from the specified object. Calls on_remove, on_dispel, or on_expire, depending on arguments.
    
    Args:
        obj:    Object to remove buff from
        id:     The buff id
        dispel: Call on_dispel when True.
        expire: Call on_expire when True.
        quiet:  Do not call on_remove when True.'''
    handler = None
    
    if id in target.db.buffs.keys(): handler = target.db.buffs
    elif id in target.db.effects.keys(): handler = target.db.effects
    else: return None

    buff: Buff = handler[id].get('ref')()
    
    packed_info = (origin, target, id, dispel, expire, quiet)

    if delay: utils.delay(delay, remove_buff, *packed_info)
    else:
        context = generate_context(target, origin, buff=id, handler=handler)

        if dispel: buff.on_dispel(context)
        elif expire: buff.on_expire(context)
        elif not quiet: buff.on_remove(context)

        del handler[id]
    
        return context

def cleanup_buffs(obj):
    '''Checks all buffs and effects on the object, and cleans up old ones.'''

    if obj.db.buffs:
        remove = [ k 
            for k,v in obj.db.buffs.items() 
            if time.time() - v.get('start') > v.get('duration') ]
        for k in remove: 
            remove_buff(obj, obj, k, expire=True)

    if obj.db.effects:
        remove = [ k 
            for k,v in obj.db.buffs.items() 
            if time.time() - v.get('start') > v.get('duration') ]
        for k in remove: 
            remove_buff(obj, obj, k, expire=True)

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
    '''Returns a list of all buffs or traits on the handler with a mod whose variable matches the value.'''
    if handler is None: return None
    
    b = []

    for v in handler:
        _ref = None
        
        if utils.inherits_from(v, Trait): _ref: Trait = v()
        else: _ref: Buff = v.get('ref')()

        if _ref.mods:
            for _m in _ref.mods:
                _m: Mod
                val = vars(_m).get(key)
                if value == val: 
                    b.append(v)
                    break

    return b

def calculate_mods(buffs: list, modifier, stat):
    '''Given a list of buffs, add all the values together.'''
    x = 0.0
    if buffs is None: return x
    
    for v in buffs:
        buff: Buff = v.get('ref')()
        for mod in buff.mods:
            mod : Mod
            if mod.modifier == modifier and mod.stat == stat:
                b = mod.base
                s = v.get('stacks')
                ps = mod.perstack

                x += b + ( (s - 1) * ps )
    return x

def find_buff(id: str, handler: dict):
    '''Checks to see if the specified buff id is on the handler.'''
    if id in handler.keys(): return True
    else: return False

def check_stat_mods(obj: Object, base: float, stat: str, quiet = False):    
    '''Finds all buffs and traits related to a stat and applies their effects.
    
    Args:
        obj: The object with a buffhandler
        base: The base value you intend to modify
        stat: The string that designates which stat buffs you want
        
    Returns the base value modified by the relevant buffs, and any messaging.'''

    # Buff cleanup to make sure all buffs are valid before processing
    cleanup_buffs(obj)

    # Buff handler assignment, so we can find the relevant buffs
    buffs = []
    traits = []
    if not obj.db.buffs and not obj.db.traits: return base
    else: 
        buffs = obj.db.buffs.values()
        traits = obj.db.traits.values()

    # Find all buffs and traits related to the specified stat.
    buff_list: list = find_mods_by_value(buffs, 'stat', stat)
    trait_list: list = find_mods_by_value(traits, 'stat', stat)
    stat_list = buff_list + trait_list

    if not stat_list: return base

    # Add all arithmetic buffs together
    add_list = find_mods_by_value(stat_list, 'modifier', 'add')
    add = calculate_mods(add_list, "add", stat)
    # obj.location.msg('Debug: (Stat: ' + stat + ', Additional: ' + str(add) + ")" )

    # Add all multiplication buffs together
    mult_list = find_mods_by_value(stat_list, 'modifier', 'mult')
    mult = calculate_mods(mult_list, "mult", stat)
    # obj.location.msg('Debug: (Stat: ' + stat + ', Multiplied: ' + str(mult) + ")" )

    # The final result
    final = (base + add) * (1.0 + mult)

    # Run the "after check" functions on all relevant buffs
    for x in stat_list:
        buff: Buff = x.get('ref')()
        context = generate_context(obj, obj, buff=buff.id, handler=obj.db.buffs)
        if not quiet: buff.after_check(context)

    return final