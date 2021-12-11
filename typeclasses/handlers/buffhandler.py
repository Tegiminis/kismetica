import time
import random

from typeclasses.buff import BaseBuff, Buff, Perk, Mod
from typeclasses.objects import Object
from evennia import utils
from typeclasses.context import BuffContext, Context, DamageContext, generate_context

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
    if target == None: target = None

    # The type reference to our buff
    _ref = buff  
    id = _ref.id

    # Create the buff dict that holds a reference and all mutable information
    b = { 'ref': _ref, 'start': time.time(), 'stacks': stacks, 'uid' : None, 'origin' : origin }     

    # Set the instance's duration. Either the buff's default duration, or one you specify
    b['duration'] = duration if duration else _ref.duration

    # Clean up the buff at the end of its duration through a delayed cleanup call
    utils.delay( b['duration'] + 0.01, cleanup_buffs, target, persistent=True )

    # Apply the buff and pass the BuffContext upwards.
    context = apply_buff(origin, target, id, b, stacks)

    return context

def apply_buff(origin: Object, target: Object, id: str, buff: dict, stacks):
    '''Apply a buff to an object, accessible by id. Returns the context for the application.'''
    handler: dict = None
    _ref = buff.get('ref')
    handler = target.db.buffs

    p_id = id
    uid = str( int( random.random() * 10000 ))

    if id in handler.keys():
        if _ref.unique: return None
        elif _ref.stacking:
            if _ref.refresh: 
                handler[p_id]['start'] = time.time()
            handler[p_id]['stacks'] = min( handler[p_id]['stacks'] + stacks, _ref.maxstacks )
        elif _ref.refresh: handler[p_id] = buff
        elif _ref.unique is False: 
            p_id = id + uid
            buff['uid'] = p_id
            handler[p_id] = buff
    else: 
        handler[p_id] = buff
    
    context: BuffContext = generate_context(origin, target, buff=handler[p_id], handler=handler)

    return context

def remove_buff(origin: Object, target: Object, id: str, dispel=False, expire=False, quiet=False, delay=0):
    '''Remove a buff or effect with matching id from the specified object. Calls on_remove, on_dispel, or on_expire, depending on arguments.
    
    Args:
        obj:    Object to remove buff from
        id:     The buff id
        dispel: Call on_dispel when True.
        expire: Call on_expire when True.
        quiet:  Do not call on_remove when True.'''
    handler = target.db.buffs
    
    if id not in handler: return None

    _buff: Buff = handler[id]['ref']()
    
    packed_info = (origin, target, id, dispel, expire, quiet)

    if delay: utils.delay(delay, remove_buff, *packed_info)
    else:
        context = generate_context(target, origin, buff=handler[id], handler=handler)

        if dispel: _buff.on_dispel(context)
        elif expire: _buff.on_expire(context)
        elif not quiet: _buff.on_remove(context)

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

    return

def view_buffs(obj) -> list:
    '''Gets the name and flavor of all buffs and effects on the object.'''
    cleanup_buffs(obj)
    message = []
    
    if obj.db.buffs:
        handler = obj.db.buffs.values()
        for x in handler:
            buff: Buff = x.get('ref')
            msg = buff.name + ": " + buff.flavor
            message.append(msg)
    
    return message

def collect_mods(handler, stat: str):
    '''Collects a list of all mods affecting the specified stat on buffs inside the specified handler.
    Vars:
        handler:    The handler list with all the buffs to search through
        stat:       The string to search for in the Mods on buffs'''
    if not handler: return None
    
    mods = []
    buffs = []

    for buff in handler:
        ref = buff['ref']

        for m in ref.mods:
            if m.stat == stat:
                stacks = 1 if 'stacks' not in buff.keys() else buff['stacks']
                packed_mod = (m, stacks)
                mods.append(packed_mod)
                buffs.append(buff)

    if not mods: return None
    else: return (buffs, mods)

def calc_packed_mods(packed_mods: list, base):
    '''Calculates a return value based on a list of packed mods (mod + stacks) and a base.'''
    add = 0
    mult = 0

    if not packed_mods: return base

    for mod in packed_mods:
        ref : Mod = mod[0]
        stacks = mod[1]
        
        if ref.modifier == 'add':   add += ref.base + ( (stacks - 1) * ref.perstack)
        if ref.modifier == 'mult':  mult += ref.base + ( (stacks - 1) * ref.perstack)
    
    final = (base + add) * (1.0 + mult)
    return final

def find_buff(id: str, handler: dict):
    '''Checks to see if the specified buff id is on the handler.'''
    if id in handler.keys(): return True
    else: return False

def check_stat_mods(obj: Object, base: float, stat: str, quiet = False):    
    '''Finds all buffs and perks related to a stat and applies their effects.
    
    Args:
        obj: The object with a buffhandler
        base: The base value you intend to modify
        stat: The string that designates which stat buffs you want
        
    Returns the base value modified by the relevant buffs, and any messaging.'''

    # Buff cleanup to make sure all buffs are valid before processing
    cleanup_buffs(obj)

    if not obj.db.buffs and not obj.db.perks: 
        # obj.location.msg('Debug: No buffs or perks found')
        return base

    # Buff handler assignment, so we can find the relevant buffs
    _traits = obj.traits

    # Find all buffs and traits related to the specified stat.
    _toApply: list = collect_mods(_traits, stat)
    # if _toApply:  obj.location.msg('Mods collected: ' + str(_toApply))

    if not _toApply: return base

    # The final result
    final = calc_packed_mods(_toApply[1], base)

    # Run the "after check" functions on all relevant buffs
    for buff in _toApply[0]:
        _handler = None
        # if 'origin' in buff.keys(): buff['origin'].location.msg('Debug Checking buff of type: ' + stat)
        ref = buff['ref']
        _handler = obj.db.buffs if isinstance(ref, Buff) else obj.db.perks 
        context = generate_context(obj, obj, buff=buff, handler=_handler)
        if not quiet: ref().after_check(context)

    return final

def add_perk(obj: Object, perk: Perk, slot: str = None):
    '''Adds the referenced perk or trait to the object's relevant handler.'''
    if perk is None: return
    
    b = { 'ref': perk }     
    
    if slot: obj.db.perks[slot] = b
    elif perk.slot: obj.db.perks[perk.slot] = b
    else: obj.db.perks[perk.id] = b     

def remove_perk(origin, target, id):
    '''Removes a perk with matching id or slot from the object's handler. Calls the perk's on_remove function.'''
    handler = target.db.perks

    if id in handler.keys():
        perk: Perk = handler[id].get('ref')()
        context = generate_context(target, origin, perk=perk, handler=handler)

        perk.on_remove(context)
        del handler[id]
        
        return context
    else: return None

def trigger_effects(self, target, trigger: str, dc : DamageContext = None) -> str:
    '''Activates all perks and effects on the origin that have the same trigger string. Returns a list of all messaging for the perks/effects.
    Vars:
        self:       The game object whose effects you wish to trigger. "origin" in BuffContext
        target:     The target of the action. "target" in BuffContext.
        trigger:    The trigger string. For an effect to trigger, it must share this trigger string
    '''
    cleanup_buffs(target)

    # self.location.msg('Triggering effects of type: ' + trigger)

    _effects = self.effects
    if _effects is None: return None

    messaging = []
    toActivate = []

    # Find all perks to trigger
    for x in _effects:
        if x['ref'].trigger == trigger:
            toActivate.append(x)
    # toActivate = [x for x in _effects if x['ref'].trigger == trigger]
    
    # Go through and trigger all relevant perks and effects, passing their trigger messages upwards.
    for x in toActivate:
        # target.location.msg("Debug Triggered Perk/Buff: " + str(x) )
        _eff : BaseBuff = x['ref']()
        _handler = None

        if isinstance(_eff, Buff): _handler = self.db.buffs
        elif isinstance (_eff, Perk): _handler = self.db.perks

        context = generate_context(self, target, buff=x, handler=_handler, dc=dc)
        trigger_context = _eff.on_trigger(context)
    
    _msg = ''
    for x in messaging: _msg += x + "\n|n"
    return _msg

def check_for_perk(target, perk) -> bool:
    '''Checks to see if the specified perk is on the object. 
    Args:
        target: The object to test
        perk:   The id string or class reference to check for

    Returns a bool.'''
    handler = target.db.perks

    if isinstance(perk, str):
        if perk in handler.keys(): return True
    elif isinstance(perk, Perk):
        for x in handler.values(): 
            if isinstance(x['ref'], perk): return True
    else: return False