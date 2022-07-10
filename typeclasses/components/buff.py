import time
from evennia import utils
from evennia.typeclasses.attributes import AttributeProperty

class BaseBuff():
    '''A buff is a self-contained object used to modify a value, trigger code, or both.
    You can freely mix them however you like.

    Buffs which have one or more Mod objects in the mods attribute can modify stats.
    You can use the handler to `check` all mods of a specific stat string and apply
    their modifications to the value. You can either do this manually (by calling
    the handler check method) or you can set up a property to do it for you automatically
    (see BuffableProperty below).

    No mods applied to the value are permanent in any way. All calculations are done at
    runtime, and the mod values are never stored anywhere except on the buff in question. In
    other words: you don't need to track the origin of particular stat mods, and you
    will never permanently change a stat modified by a trait buff. To remove the modification,
    remove the buff off the object.

    Buffs which have one or more strings in the `triggers` attribute can be triggered by events. 
    Effects allow buffs to react to the game state.
    
    For example, let's say I want to trigger all "hit" buffs on myself when I successfully
    hit a target. I add `self.handler.trigger("hit")` to the relevant point in my attack code.
    Now, whenever I land a successful hit, the buffs are triggered and run their on_trigger method.

    Regardless of triggers or mods, buffs also have the following qualities:
        - They can stack. If a buff's `maxstacks` is greater than 1, if will stack with any buff with
        the same key on that handler. Buffs which are not `unique` will be separated according to
        the object that applied them.
        - They have a `duration`, and automatically clean up at the end of it (0 duration = forever).
        - They handle timing. They remember when they were applied, and can be paused, resumed, and refreshed.
        - They can tick. They keep track of how many ticks have happened, and continue ticking until removed

    Buffs are stored in two parts: as an immutable reference to the buff class, and as cached mutable data.
    You can store any information you like in the cache - by default, it's all the basic timing and event
    information necessary for the system to run.
    '''
    
    key = 'template'        # The buff's unique key. Will be used as the buff's key in the handler
    name = 'Template'       # The buff's name. Used for user messaging
    flavor = 'Template'     # The buff's flavor text. Used for user messaging
    isvisible = True        # If the buff is considered "visible" to the "view" method

    triggers = []       # The effect's trigger strings, used for functions.

    duration = 0        # Default buff duration; 0 or lower for permanent buff

    refresh = True      # Does the buff refresh its timer on application?
    unique = True      # Does the buff overwrite existing buffs with the same key on the same target?
    maxstacks = 1       # The maximum number of stacks the buff can have. If >1, this buff will stack.
    tickrate = 0        # How frequent does this buff tick, in seconds (cannot be lower than 1)
    
    mods = []   # List of mod objects. See Mod class below for more detail

    @property
    def ticknum(self):
        '''Returns how many ticks this buff has gone through as an integer.'''
        x = (time.time() - self.start) / self.tickrate
        return int(x)

    @property
    def owner(self):
        return self.handler.obj

    @property
    def ticks(self)-> bool:
        '''Returns if this buff ticks or not (tickrate => 1)'''
        return self.tickrate >= 1

    @property
    def stacking(self) -> bool:
        '''Returns if this buff stacks or not (maxstacks > 1)'''
        return self.maxstacks > 1

    def __init__(self, handler, uid) -> None:
        self.handler: BuffHandler = handler
        self.uid = uid
        
        cache:dict = handler.db.get(uid)
        self.start = cache.get('start')
        self.prevtick = cache.get('prevtick')
        self.paused = cache.get('paused')
        self.stacks = cache.get('stacks')
        self.source = cache.get('source')

    def remove(self, loud=True, dispel=False, delay=0, context={}):
        '''Helper method which removes this buff from its handler.'''
        self.handler.remove(self.uid, loud, dispel, delay, context)

    def dispel(self, dispel=True, loud=True, delay=0, context={}):
        '''Helper method which dispels this buff (removes and calls on_dispel).'''
        self.handler.remove(self.uid, loud, dispel, delay, context)

    def pause(self):
        '''Helper method which pauses this buff on its handler.'''
        self.handler.pause(self.uid)

    def unpause(self):
        '''Helper method which unpauses this buff on its handler.'''
        self.handler.unpause(self.uid)

    def conditional(self, *args, **kwargs):
        '''Hook function for conditional stat mods. This must return True in 
        order for a mod to be applied, or a trigger to fire.'''
        return True

    def on_apply(self, *args, **kwargs):
        '''Hook function to run when this buff is applied to an object.'''
        pass
    
    def on_remove(self, *args, **kwargs):
        '''Hook function to run when this buff is removed from an object.'''
        pass

    def on_remove_stack(self, *args, **kwargs):
        '''Hook function to run when this buff loses stacks.'''
        pass

    def on_dispel(self, *args, **kwargs):
        '''Hook function to run when this buff is dispelled from an object (removed by someone other than the buff holder).'''
        pass

    def on_expire(self, *args, **kwargs):
        '''Hook function to run when this buff expires from an object.'''
        pass

    def after_check(self, *args, **kwargs):
        '''Hook function to run after this buff's mods are checked.'''
        pass

    def on_trigger(self, trigger:str, *args, **kwargs):
        '''Hook for the code you want to run whenever the effect is triggered.
        Passes the trigger string to the function, so you can have multiple
        triggers on one buff.'''
        pass

    def on_tick(self, initial, *args, **kwargs):
        '''Hook for actions that occur per-tick, a designer-set sub-duration.'''
        pass

class Mod():
    '''A single stat mod object. One buff or trait can hold multiple mods, for the same or different stats.'''
    
    stat = 'null'       # The stat string that is checked to see if this mod should be applied  
    value = 0            # Buff's value
    perstack = 0        # How much additional value is added to the buff per stack
    modifier = 'add'    # The modifier the buff applies. 'add' or 'mult' 

    def __init__(self, stat: str, modifier: str, value, perstack=0.0) -> None:
        '''
        Args:
            stat:       The stat the buff affects. Normally matches the object attribute name
            mod:        The modifier the buff applies. "add" for add/sub or "mult" for mult/div  
            value:      The value of the modifier
            perstack:   How much is added to the base, per stack (including first).'''
        self.stat = stat
        self.modifier = modifier
        self.value = value
        self.perstack = perstack

class BuffHandler(object):
    '''This is the handler for your buffs. You should add this as a @lazy_property to any object
    you want to utilize buffs. You may optionally do so with a dbkey, so you can have multiple buff
    systems that do not overlap (for example: perks vs buffs) without having to create multiple
    BuffHandler classes.

    Context is an important concept for this handler. Every method which modifies, triggers, or
    checks a buff optionally feeds a `context` dictionary (default: empty) to the buff hook methods as keyword 
    arguments. This makes those methods "event-aware".
    
    For example, let's say you want a "thorns" buff which damages enemies that attack you. In your character's 
    "take damage" method, you create a dictionary with the value {"attacker":attacker}, and trigger the
    character's "damaged" buffs with your dictionary as the `context` argument. Then, in your thorns 
    buff, you add "attacker" as an `on_trigger` argument, and write whatever retaliation code you like. Apply
    the buff and watch it work!

    The handler itself has only a few attributes:
        - the `obj` it is attached to. This is passed when you define it as a @lazy_property.
        - the `dbkey` used for the handler's data. Defaults to "buffs" if you don't define it with the @lazy_property

    You can access buffs on this handler in a number of ways, all of which return either the buff or a dictionary of buffs:
        - You can use `handler.buffname`, as long as the buff's key isn't already used in the handler's namespace.
        - You can call the `traits` and `effects` properties, which find ALL trigger and modifier buffs respectively
        - You can call several `get` methods for different slices of buffs; keys, type, stat value, trigger, and cache value
    '''

    obj = None
    dbkey = "buffs"
    
    def __init__(self, obj, dbkey=dbkey):
        self.obj = obj
        self.dbkey = dbkey

    def __getattr__(self, __name: str):
       return self.get(__name)

    #region properties
    @property
    def db(self):
        '''The object attribute we use for the buff database. Auto-creates if not present. 
        Convenience shortcut (equal to self.obj.db.dbkey)'''
        if not self.obj.attributes.has(self.dbkey): self.obj.attributes.add(self.dbkey, {})
        return self.obj.attributes.get(self.dbkey)

    @property
    def traits(self):
        '''All buffs on this handler that modify a stat.'''
        _t = {k:self.get(k) for k,v in self.db.items() if v['ref'].mods}
        return _t

    @property
    def effects(self):
        '''All buffs on this handler that trigger off an event.'''
        _e = {k:self.get(k) for k,v in self.db.items() if v['ref'].triggers}
        return _e

    @property
    def playtime(self):
        '''All buffs on this handler that only count down during active playtime.'''
        _pt = {k:self.get(k) for k,v in self.db.items() if v['ref'].playtime}
        return _pt

    @property
    def paused(self):
        '''All buffs on this handler that are paused.'''
        _p = {k:self.get(k) for k,v in self.db.items() if v['paused'] == True}
        return _p

    @property
    def expired(self):
        '''All buffs on this handler that have expired.'''
        _e = { k: self.get(k) 
            for k,v in self.db.items()
            if not v['paused']
            if v['duration'] > 0 
            if v['duration'] < time.time() - v['start'] }
        return _e

    @property
    def all(self):
        '''Returns dictionary of instanced buffs equivalent to ALL buffs on this handler, 
        regardless of state, type, or anything else. You will only need this to extend 
        handler functionality. It is otherwise unused.'''
        _a = {k:self.get(k) for k,v in self.db.items()}
        return _a
    #endregion
    
    #region methods
    def add(self, buff: BaseBuff, key:str=None,
        stacks=1, duration=None, source=None,
        context={}, *args, **kwargs
        ):
        
        '''Add a buff to this object, respecting all stacking/refresh/reapplication rules. Takes
        a number of optional parameters to allow for customization.
        
        Args:
            buff:       The buff class you wish to add
            source:     (optional) The source of this buff.
            stacks:     (optional) The number of stacks you want to add, if the buff is stacking
            duration:   (optional) The amount of time, in seconds, you want the buff to last. 
            context:    (optional) An existing context you want to add buff details to
        '''
        
        _context = context
        source = self.obj

        # Create the buff dict that holds a reference and all runtime information.
        b = { 
            'ref': buff,
            'start': time.time(),
            'duration': buff.duration, 
            'prevtick': None,
            'paused': False, 
            'stacks': stacks,  
            'source': source }

        # Generate the pID (procedural ID) from the object's dbref (uID) and buff key. 
        # This is the actual key the buff uses on the dictionary
        uid = key
        if not uid:
            if source: mix = str(source.dbref).replace("#","")
            uid = buff.key if buff.unique is True else buff.key + mix
        
        # If the buff is on the dictionary, we edit existing values for refreshing/stacking
        if uid in self.db.keys(): 
            b = dict( self.db[uid] )
            if buff.refresh: b['start'] = time.time()
            if buff.maxstacks>1: b['stacks'] = min( b['stacks'] + stacks, buff.maxstacks )
        
        # Setting duration and initial tick, if relevant
        b['prevtick'] = time.time() if buff.tickrate>=1 else None
        if duration: b['duration'] = duration

        # Apply the buff!
        self.db[uid] = b

        # Create the buff instance and run the on-application hook method
        instance: BaseBuff = self.get(uid)
        instance.on_apply(**_context)
        if instance.ticks: tick_buff(self, uid, _context)
        
        # Clean up the buff at the end of its duration through a delayed cleanup call
        utils.delay( b['duration'], cleanup_buffs, self, persistent=True )

        # Apply the buff and pass the Context upwards.
        # return _context

    def remove(self, buffkey, 
        loud=True, dispel=False, expire=False, 
        context={}, *args, **kwargs
        ):
        '''Remove a buff or effect with matching key from this object. Normally calls on_remove,
        calls on_expire if the buff expired naturally, and optionally calls on_dispel.
        
        Args:
            key:    The buff key
            loud:   Calls on_remove when True. Default remove hook.
            dispel: Calls on_dispel when True
            expire: Calls on_expire when True. Used when cleaned up.
'''

        if buffkey not in self.db: return None
        
        _context = context
        buff: BaseBuff = self.db[buffkey]['ref']
        instance : BaseBuff = buff(self, buffkey)
        
        if loud:
            if dispel: instance.on_dispel(**context)
            elif expire: instance.on_expire(**context)
            instance.on_remove(**context)

        del instance
        del self.db[buffkey]

        return _context
    
    def remove_by_type(self, bufftype:BaseBuff, 
        loud=True, dispel=False, expire=False, 
        context={}, *args, **kwargs
        ):
        '''Removes all buffs of a specified type from this object'''
        _remove = self.get_by_type(bufftype)
        if not _remove: return None

        _context = context
        for k,instance in _remove.items():
            instance: BaseBuff        
            if loud:
                if dispel: instance.on_dispel(**context)
                elif expire: instance.on_expire(**context)
                instance.on_remove(**context)
            del instance
            del self.db[k]

        return _context
        

    def get(self, buffkey: str):
        '''If the specified key is on this handler, return the instanced buff. Otherwise return None.
        You should delete this when you're done with it, so that garbage collection doesn't have to.'''
        _return = None
        _b = self.db.get(buffkey)
        if _b: _return = _b["ref"](self, buffkey)
        return _return

    def get_by_type(self, buff:BaseBuff):
        '''Returns a dictionary of instanced buffs of the specified type in the format {uid: instance}.'''
        return {k: self.get(k) for k,v in self.db.items() if v['ref'] == buff}

    def get_by_stat(self, stat:str, context={}):
        '''Returns a dictionary of instanced buffs which modify the specified stat in the format {uid: instance}.'''
        _cache = self.traits
        if not _cache: return None

        buffs = {k:buff 
                for k,buff in _cache.items() 
                for m in buff.mods
                if m.stat == stat 
                if not buff.paused
                if buff.conditional(**context)}
        return buffs

    def get_by_trigger(self, trigger:str, context={}):
        '''Returns a dictionary of instanced buffs which fire off the designated trigger, in the format {uid: instance}.'''
        _cache = self.effects
        return {k:buff 
            for k,buff in _cache.items() 
            if trigger in buff.triggers
            if not buff.paused
            if buff.conditional(**context)}

    def get_by_cachevalue(key:str, value):
        '''Returns a dictionary of instanced buffs which have the associated key:value in their cache, in the format {uid: instance}.'''
        pass

    def check(self, value: float, stat: str, loud=True, context={}):    
        '''Finds all buffs and perks related to a stat and applies their effects.
        
        Args:
            value: The value you intend to modify
            stat: The string that designates which stat buffs you want
            
        Returns the value modified by relevant buffs.'''
        # Buff cleanup to make sure all buffs are valid before processing
        self.cleanup()

        # Find all buffs and traits related to the specified stat.
        applied = self.get_by_stat(stat)
        if not applied: return value

        # The final result
        final = self._calculate_mods(value, stat, applied)

        # Run the "after check" functions on all relevant buffs
        for buff in applied.values():
            buff: BaseBuff
            if loud: buff.after_check(**context)
            del buff
        return final
    
    def trigger(self, trigger: str, context:dict = {}):
        '''Activates all perks and effects on the origin that have the same trigger string. 
        Takes a trigger string and a dictionary that is passed to the buff as kwargs.
        '''
        self.cleanup()
        _effects = self.get_by_trigger(trigger, context)
        if _effects is None: return None

        # Trigger all buffs whose trigger matches the trigger string
        for buff in _effects.values():
            buff: BaseBuff
            if trigger in buff.triggers and not buff.paused:
                buff.on_trigger(trigger, **context)
    
    def pause(self, key: str):
        """Pauses the buff. This excludes it from being checked for mods, triggered, or cleaned up. 
        Used to make buffs 'playtime' instead of 'realtime'."""
        if key in self.db.values():
            # Mark the buff as paused
            buff = self.db[key]
            buff['paused'] = True

            # Figure out our new duration
            t = time.time()         # Current Time
            s = buff['start']       # Start
            d = buff['duration']    # Duration
            e = s + d               # End
            nd = e - t              # New duration

            # Apply the new duration
            if nd > 0: buff['duration'] = nd 
            else: self.remove(key)
        return

    def unpause(self, key: str):
        '''Unpauses a buff. This makes it visible to the various buff systems again.'''
        if key in self.db.values():
            # Mark the buff as unpaused
            buff = self.db[key]
            buff['paused'] = False

            # Start our new timer
            buff['start'] = time.time()
            utils.delay( buff['duration'] + 0.01, cleanup_buffs, self, persistent=True )
        return

    def view(self) -> list:
        '''Gets the name and flavor of all buffs and effects on the object.'''
        self.cleanup()
        message = []
        
        if self.db:
            _cache = self.db.values()
            for x in _cache:
                buff: BaseBuff = x.get('ref')
                msg = "    " + buff.name + ": " + buff.flavor
                message.append(msg)
        
        return message

    def cleanup(self):
        '''Cleans up all old buffs on this handler.'''
        cleanup_buffs(self)

    #region private methods
    def _calculate_mods(self, value, stat:str, buffs:dict):
        '''Calculates a return value from a base value, a stat string, and a dictionary of instanced buffs.'''
        if not buffs: return value
        add = 0
        mult = 0

        for buff in buffs.values():
            for mod in buff.mods:
                buff:BaseBuff
                mod:Mod
                if mod.stat == stat:    
                    if mod.modifier == 'add':   add += mod.value + ( (buff.stacks) * mod.perstack)
                    if mod.modifier == 'mult':  mult += mod.value + ( (buff.stacks) * mod.perstack)
        
        final = (value + add) * (1.0 + mult)
        return final
    #endregion
    #endregion   

class BuffableProperty(AttributeProperty):
    '''An example of a way you can extend AttributeProperty to create properties that automatically check buffs for you.'''
    def at_get(self, value, obj):
        _value = obj.buffs.check(value, self._key)
        return _value

def cleanup_buffs(handler: BuffHandler):
    '''Cleans up all expired buffs from a handler.'''
    _remove = handler.expired
    for v in _remove.values(): v.remove(expire=True)

def tick_buff(obj, handler: BuffHandler, uid: str, context={}, initial=True):
    '''Ticks a buff. If a buff's tickrate is 1 or larger, this is called when the buff is applied, and then once per tick cycle.'''
    # Cache a reference and find the buff on the object
    _cache = handler.db
    if uid not in _cache.keys(): return
    b = dict(_cache[uid])

    # Instantiate the buff and tickrate
    buff: BaseBuff = b['ref'](obj, handler, uid, b)
    tr = buff.tickrate
    
    # This stops the old ticking process if you refresh/stack the buff
    if tr > time.time() - buff.prevtick and initial is not True: return     
    
    # If the duration has run out, tick one last time, then stop this process
    if buff.duration < time.time() - buff.start:
        if tr < time.time() - buff.prevtick: buff.on_tick(initial, **context)
        return

    # If it's time, call the buff's on_tick method and update prevtick
    if tr < time.time() - buff.prevtick: buff.on_tick(initial, **context)
    
    _cache[uid]['prevtick'] = time.time()

    # Recur this function at the tickrate interval, if it didn't stop/fail
    utils.delay(tr, tick_buff, obj=obj, handler=handler, uid=uid, context=context, initial=False)