import time
import random
from evennia import utils, TICKER_HANDLER
from typeclasses.objects import DefaultObject as Object
from typeclasses.context import Context

class BaseBuff():
    '''Base class for all "buffs" in the game. Buffs are permanent and temporary modifications to stats, and trigger conditions that run arbitrary code.

    Strings:
        id:         The buff's unique ID. Will be used as the buff's key in the handler
        name:       The buff's name. Used for user messaging
        flavor:     The buff's flavor text. Used for user messaging
        trigger:    The buff's trigger string. Used for effects
        release:    The buff's release string. Used for effects
    '''
    
    id = 'template'             # The buff's unique ID. Will be used as the buff's key in the handler
    name = 'Template'           # The buff's name. Used for user messaging
    flavor = 'Template'         # The buff's flavor text. Used for user messaging

    trigger = None        # The effect's trigger string, used for functions
    release = None        # The effect's release string, used for functions

    trigger_msg = None

    cooldown = 0

    mods = None

    def on_apply(self, context: Context) -> Context:
        '''Hook function to run when this buff is applied to an object.'''
        pass
    
    def on_remove(self, context: Context) -> Context:
        '''Hook function to run when this buff is removed from an object.'''
        pass

    def on_remove_stack(self, context: Context) -> Context:
        '''Hook function to run when this buff loses stacks.'''
        pass

    def on_dispel(self, context: Context) -> Context:
        '''Hook function to run when this buff is dispelled from an object (removed by someone other than the buff holder).'''
        pass

    def on_expire(self, context: Context) -> Context:
        '''Hook function to run when this buff expires from an object.'''
        pass

    def after_check(self, context: Context) -> Context:
        '''Hook function to run after this buff's mods are checked.'''
        pass

    def on_trigger(self, context: Context) -> Context:
        '''Hook for the code you want to run whenever the effect is triggered. Required.'''
        pass

    def on_release(self, context: Context) -> Context:
        '''Hook for the code you want to run whenever the effect is released (reverse of trigger). Optional.'''
        pass

    def on_tick(self, context: Context) -> Context:
        '''Hook for actions that occur per-tick, a designer-set sub-duration.'''
        pass

class Buff(BaseBuff):
    '''A buff is comprised of one or more temporary stat modifications or trigger effects. Includes a duration, stack size, and so on.

    Strings:
        id:         The buff's unique ID. Will be used as the buff's key in the handler
        name:       The buff's name. Used for user messaging
        flavor:     The buff's flavor text. Used for user messaging
    Vars:
        duration:   Buff duration in seconds. Will use this if the add_buff keyword is not overloaded. -1 for a "permanent" buff
        maxstacks:  The maximum number of stacks the buff can have.
        mods:       The modifiers the buff applies. See Mod class.
    Bools:
        refresh (True):     Does the buff refresh its timer on application?
        stacking (False):   Does the buff stack with itself?
        unique (False):     Will this buff prevent reapplication until its duration is out?'''
    
    duration = 1                # Buff duration in seconds. Will use this if the buffhandler add method is not overloaded. -1 for a "permanent" buff

    refresh = True              # Does the buff refresh its timer on application?
    stacking = False            # Does the buff stack with itself?
    unique = False              # Does the buff overwrite existing buffs with the same ID on the same target?
    maxstacks = 1               # The maximum number of stacks the buff can have.

    ticking = False
    tickrate = 5

class Perk(BaseBuff):
    '''A permanent buff. Uses "slot" for the id in the dict.
    
    Strings:
        id:         The perk's unique ID. Will be used as the perk's key in the handler
        name:       The perk's name. Used for user messaging
        flavor:     The perk's flavor text. Used for user messaging
    Vars:
        slot:       If defined, uses this for the perk's dictionary key. Otherwise, uses the perk id.
        trigger:    Trigger string, used to activate it through the perk handler.
        release:    Release string, currently unused.
    Funcs:
        on_trigger: Hook for code to run when the perk is triggered. Required.
        on_release: Hook for code to run when the perk is released.
    '''

    slot = None

class Mod():
    '''A single stat modification. One buff or trait can hold multiple mods, for the same or different stats.'''
    
    stat = 'damage'             # The stat the buff affects. Essentially a tag used to find the buff for coding purposes  
    base = 0                    # Buff's value
    perstack = 0                # How much additional value is added to the buff per stack
    modifier = 'add'            # The modifier the buff applies. 'add' or 'mult' 

    def __init__(self, stat: str, modifier: str, base, perstack = 0) -> None:
        '''
        Args:
            stat:       The stat the buff affects. Essentially a tag used to find the buff for coding purposes
            mod:        The modifier the buff applies. "add" for add/sub or "mult" for mult/div  
            base:       Buff's value
            perstack:   How much additional value is added to the buff per stack'''
        self.stat = stat
        self.modifier = modifier
        self.base = base
        self.perstack = perstack

class BuffHandler(object):

    obj = None
    
    def __init__(self, obj):
        self.obj = obj
        if not self.obj.attributes.has('buffs'): self.obj.db.buffs = {}

    @property
    def db(self):
        return self.obj.db.buffs
    
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

        b['prevtick'] = time.time() if _ref.ticking else None
        b['duration'] = duration if duration else _ref.duration

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
            tick_buff(handler[_id], context)

        # Clean up the buff at the end of its duration through a delayed cleanup call
        utils.delay( b['duration'] + 0.01, cleanup_buffs, self.obj, persistent=True )

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
            if dispel: instance.on_dispel(context)
            elif expire: instance.on_expire(context) 

            instance.on_remove(context)

        del instance
        del handler[id]
    
        return context

    def cleanup(self):
        '''Cleans up all old buffs on this object'''
        cleanup_buffs(self.obj)

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

        # Find all buffs and traits related to the specified stat.
        _toApply: tuple = self._collect_mods(stat)
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
    
    def find(self, buff: BaseBuff):
        '''Finds the specified buff on this object, if it exists. Returns a boolean.'''
        for b in self.db:
            if b['ref'] == buff: return True
        return False

    
    def trigger(self, trigger: str, source=None, target=None, context:Context = None) -> str:
        '''Activates all perks and effects on the origin that have the same trigger string. Returns a list of all messaging for the perks/effects.
        Vars:
            trigger:    The trigger string. For an effect to trigger, it must share this trigger string
            source:     (optional) The object activating this trigger
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
                target = target if target is not None else self.obj

                context = Context(origin, target, buff=x, handler=_handler)
            
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

    def _calc_packed_mods(self, packed_mods: list, base):
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

class PerkHandler(object):

    obj = None
    
    def __init__(self, obj):
        self.obj = obj
        if not self.obj.attributes.has('perks'): self.obj.db.perks = {}

    @property
    def db(self):
        return self.obj.db.perks

    def add(self: Object, perk: Perk, slot: str = None):
        '''Adds the referenced perk or trait to the object's relevant handler.'''
        if perk is None: return
        
        b = { 'ref': perk }     
        
        if slot: self.db[slot] = b
        elif perk.slot: self.db[perk.slot] = b
        else: self.db[perk.id] = b     

    def remove(self, id, source=None) -> Context:
        '''Removes a perk with matching id or slot from the object's handler. Calls the perk's on_remove function.'''
        origin = source if source is not None else self.obj
        if id in self.db.keys():
            perk = self.db[id]['ref']
            context = Context(origin, self.obj, perk=perk, handler=self.db)

            instance: Perk = perk()
            instance.on_remove(context)
            del self.db[id]
            del instance
            
            return context
        else: return None

def cleanup_buffs(obj):
    _buffs = dict(obj.db.buffs)
    if _buffs:
            remove = [ k 
                for k,v in _buffs.items() 
                if v['duration'] < time.time() - v['start'] ]
            for k in remove: 
                obj.buffs.remove(k, expire=True)

def tick_buff(buff: dict, context: Context, initial=True):
        '''Ticks a buff. If a buff's ticking value is True, this is called when the buff is applied, and then once per tick cycle.'''

        _buffs = context.target.db.buffs
        if context.buffID in _buffs.keys(): 
            context.buff = _buffs[context.buffID]
            buff = _buffs[context.buffID]

        ref: BaseBuff = buff['ref']()
        _tr = ref.tickrate

        if _tr > time.time() - context.buffPrevTick and initial is not True: return
        
        if context.buffDuration < time.time() - context.buffStart:
            if _tr < time.time() - context.buffPrevTick: ref.on_tick(context)
            return
        if context.buffID not in context.target.buffs.db.keys(): 
            context.origin.msg("Debug: No ticking buff found") 
            return

        if _tr < time.time() - context.buffPrevTick: 
            ref.on_tick(context)
        # context.origin.msg("Debug: Attempting to defer tick call") 
        buff['prevtick'] = time.time()
        utils.delay(_tr, tick_buff, buff=context.buff, context=context, initial=False)