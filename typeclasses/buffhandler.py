import time
import random
import copy

from typeclasses.buff import BaseBuff, Buff, Perk, Mod
from typeclasses.objects import Object
from evennia import utils
from typeclasses.context import Context

class BuffHandler(object):

    obj = None
    
    def __init__(self, obj):
        self.obj = obj
        self.db = self.obj.db.buffs

    def add(
        self,
        buff: BaseBuff,
        id = None,
        source = None, 
        stacks = 1, 
        duration = None, 
        context = None
        ):
        
        '''Add a buff or effect instance to this object, respecting all stacking/refresh/reapplication rules.
        
        Args:
            buff:       The buff class you wish to add
            id:         (optional) The id you want this buff to use
            source:     (optional) The source of this buff.
            stacks:     (optional) The number of stacks you want to add, if the buff is stacking
            duration:   (optional) The amount of time, in seconds, you want the buff to last.
            context:    (optional) An existing context you want to add buff details to
        
        Returns the buff context for the action.
        '''

        self.cleanup()

        _ref: Buff = buff  
        _id = _ref.id if id is None else id
        _context: Context = context if context else None
        handler = self.db
        

        # Create the buff dict that holds a reference and all runtime information.
        b = { 
            'ref': _ref,
            'uid': None, 
            'start': time.time(),
            'duration': duration, 
            'prevtick': None, 
            'stacks': stacks,  
            'source': source }
        
        b['prevtick'] = time.time() if _ref.ticking else None
        b['duration'] = duration if duration else _ref.duration

        uid = str( int( random.random() * 10000 ))
        pid = _id + uid

        if _id in handler.keys(): 
            if _ref.unique: 
                b = dict( handler[_id] )
                if _ref.refresh: b['start'] = time.time()
                if _ref.stacking: b['stacks'] = min( b['stacks'] + stacks, _ref.maxstacks )
            if _ref.unique is False: 
                b['uid'] = pid
                _id = pid

        
        handler[_id] = b

        
        if context: _context.buff = b
        else: 
            _origin = source if source is not None else self.obj
            _context = Context(_origin, self.obj, buff=b, handler=self.db)

        _tr = _ref.tickrate

        instance: BaseBuff = _ref()
        instance.on_apply(_context)
        del instance

        if _ref.ticking:
            # utils.delay(_tr, tick_buff, persistent=True, buff=buff, context=context)
            self.tick_buff(b, context)
            context.origin.msg("Debug: Applying a ticking buff")

        # Clean up the buff at the end of its duration through a delayed cleanup call
        utils.delay( b['duration'] + 0.01, self.cleanup, persistent=True )

        # Apply the buff and pass the Context upwards.
        return _context

    def remove(
        self, 
        id,
        source=None, 
        dispel=False, 
        expire=False, 
        quiet=False, 
        delay=0
        ):
        '''Remove a buff or effect with matching id from this object. Calls on_remove, on_dispel, or on_expire, depending on arguments.
        
        Args:
            obj:    Object to remove buff from
            id:     The buff id
            dispel: Call on_dispel when True.
            expire: Call on_expire when True.
            quiet:  Do not call on_remove when True.'''
        
        handler = self.db
        
        if id not in handler: return None
    
        buff: Buff = handler[id]['ref']
        instance = buff()
        
        origin = source if source is not None else self.obj
        context = Context(origin, self.obj, buff=handler[id], handler=handler)
        
        if not quiet:
            if dispel: buff.on_dispel(context)
            elif expire: buff.on_expire(context) 

            buff.on_remove(context)

        del instance
        del handler[id]
    
        return context

    def cleanup(self):
        '''Cleans up all old buffs on this object'''
        if self.db:
            remove = [ k 
                for k,v in self.db.items() 
                if v['duration'] < time.time() - v['start'] ]
            for k in remove: 
                self.remove(k, expire=True)

    def view(self) -> list:
        '''Gets the name and flavor of all buffs and effects on the object.'''
        self.cleanup()
        message = []
        
        if self.db:
            handler = self.db.values()
            for x in handler:
                buff: Buff = x.get('ref')
                msg = buff.name + ": " + buff.flavor
                message.append(msg)
        
        return message

    def check(self, base: float, stat: str, quiet = False):    
        '''Finds all buffs and perks related to a stat and applies their effects.
        
        Args:
            base: The base value you intend to modify
            stat: The string that designates which stat buffs you want
            
        Returns the base value modified by relevant buffs, and any messaging.'''

        # Buff cleanup to make sure all buffs are valid before processing
        self.obj.buffs.cleanup()
        _traits = self.traits

        if not _traits: 
            # self.location.msg('Debug: No buffs or perks found')
            return base

        # Find all buffs and traits related to the specified stat.
        _toApply: tuple = self._collect_mods(_traits, stat)
        # if _toApply:  obj.location.msg('Mods collected: ' + str(_toApply))

        if not _toApply: return base

        # The final result
        final = self._calc_packed_mods(_toApply[1], base)

        # Run the "after check" functions on all relevant buffs
        for buff in _toApply[0]:
            # if 'origin' in buff.keys(): buff['origin'].location.msg('Debug Checking buff of type: ' + stat)
            instance = buff['ref']()
            _handler = self.db if isinstance(instance, Buff) else self.obj.db.perks 
            context = Context(self.obj, self.obj, buff=buff, handler=_handler)
            if not quiet: instance.after_check(context)
            del instance

        return final
    
    def trigger(self, trigger: str, source=None, context:Context = None) -> str:
        '''Activates all perks and effects on the origin that have the same trigger string. Returns a list of all messaging for the perks/effects.
        Vars:
            trigger:    The trigger string. For an effect to trigger, it must share this trigger string
            source:     (optional) The object removing this perk
        '''
        self.cleanup()

        # self.location.msg('Triggering effects of type: ' + trigger)

        _effects = self.obj.effects
        if _effects is None: return None

        toActivate = []

        # Find all perks to trigger
        for x in _effects:
            if x['ref'].trigger == trigger:
                toActivate.append(x)
        # toActivate = [x for x in _effects if x['ref'].trigger == trigger]
        
        # Go through and trigger all relevant perks and effects, passing their trigger messages upwards.
        for x in toActivate:
            # target.location.msg("Debug Triggered Perk/Buff: " + str(x) )
            _eff : BaseBuff = x['ref']
            instance = _eff()

            if isinstance(_eff, Buff): _handler = self.db
            else: _handler = self.obj.db.perks

            if context:
                context.buff = x
                context.buffHandler = _handler
            else: 
                origin = source if source is not None else self.obj
                context = Context(origin, self.obj, buff=x, handler=_handler)
            
            # origin.location.msg("Debug Weapon Context: " + str(_context.weapon))
            triggerContext = instance.on_trigger(context)
            del instance

    def _collect_mods(self, stat: str):
        '''Collects a list of all mods affecting the specified stat on buffs affect this object.
        Vars:
            stat:       The string to search for in the Mods on buffs'''
        handler = self.obj.traits
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

    def _calc_packed_mods(packed_mods: list, base):
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

    def tick_buff(self, buff: dict, context: Context):
        '''Ticks a buff. If a buff's ticking value is True, this is called when the buff is applied, and then once per tick cycle.
        First, checks to see if buff is valid still. 
        Then, calls the buff's on_tick method
        Finally, sets up a recursive delay call to this function.'''

        _ref: BaseBuff = buff['ref']
        _tr = _ref.tickrate

        context.origin.msg("Debug: Attempting to tick a buff")
        context.origin.msg("Debug: Remaining buff duration: " + str(context.buffDuration - (time.time() - context.buff['start'])))
        
        if context.buffDuration < time.time() - context.buffStart: 
            if _tr < time.time() - context.buffLastTick: _ref().on_tick(context)
            return
        if context.buffID not in context.buffHandler.keys(): return

        if _tr < time.time() - context.buffLastTick: _ref().on_tick(context)
        utils.delay(_tr, self.tick_buff, buff=context.buff, context=context)