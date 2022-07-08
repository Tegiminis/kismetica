import time
from evennia import utils
from evennia.typeclasses.attributes import AttributeProperty

class BaseBuff():
    '''Base class for all "buffs" in the game. Buffs are permanent and temporary modifications to stats, and trigger conditions that run arbitrary code.

    Strings:
        key:        The buff's unique key. Will be used as the buff's key in the handler
        name:       The buff's name. Used for user messaging
        flavor:     The buff's flavor text. Used for user messaging
        trigger:    The buff's trigger string. Used for effects
        release:    The buff's release string. Used for effects

    Bools:
        isvisible:  Is the buff visible to the "view" method?
        refresh:    Does the buff refresh when re-applied over an existing buff?
        stacking:   Does the buff stack?
        unique:     Is the buff "unique"? If True, uses the buff's key for the db key; if False, uses the buff's key + the source dbref.
        ticking:    Does the buff tick?

    Nums:
        duration:   Default duration of buff in seconds.
        maxstacks:  Maximum number of stacks
        tickrate:   Tick rate of buff in seconds
        cooldown:   Cooldown of buff in seconds

    Properties:
        start:      When this buff started
        stacks:     How many stacks this buff has
        duration:   The duration of the buff, in seconds. Can differ from the default duration.
        prevtick:   The last time this buff ticked
        ticknum:    How many times this buff has ticked
    
    Methods:
        remove:     Removes this buff from the handler
        pause:      Pauses this buff, which prevents it from counting down until it is unpaused.
    '''
    
    key = 'template'        # The buff's unique key. Will be used as the buff's key in the handler
    name = 'Template'       # The buff's name. Used for user messaging
    flavor = 'Template'     # The buff's flavor text. Used for user messaging
    isvisible = True        # If the buff is considered "visible" to the "view" method

    trigger = None      # The effect's trigger string, used for functions

    duration = 0        # Default buff duration; 0 or lower for permanent buff

    refresh = True      # Does the buff refresh its timer on application?
    stacking = False    # Does the buff stack with itself?
    unique = False      # Does the buff overwrite existing buffs with the same key on the same target?
    maxstacks = 1       # The maximum number of stacks the buff can have.

    ticking = False     # Does this buff tick?
    tickrate = 5        # How frequent does this buff tick, in seconds (cannot be lower than 1)
    cooldown = 0        # Duration in seconds before this buff can be checked/triggered again    
    
    mods = []   # List of mod objects. See Mod class below for more detail

    @property
    def ticknum(self):
        '''Returns how many ticks this buff has gone through as an integer.'''
        x = (time.time() - self.start) / self.tickrate
        return int(x)

    def __init__(self, owner, handler, pid, data: dict) -> None:
        self.owner = owner
        self.handler = handler
        self.pid = pid
        self.start = data.get('start')
        self.duration = data.get('duration')
        self.prevtick = data.get('prevtick')
        self.paused = data.get('paused')
        self.stacks = data.get('stacks')
        self.source = data.get('source')

    def remove(self, dispel=False, expire=False, loud=True, delay=0, context={}):
        '''Helper method which removes this buff from its handler.'''
        self.handler.remove(self.pid, dispel, expire, loud, delay, context)

    def pause(self):
        '''Helper method which pauses this buff on its handler.'''
        pass

    def conditional(self, *args, **kwargs):
        '''Hook function for conditional stat mods. This must return True in order for a mod to be applied.'''
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

    def on_trigger(self, *args, **kwargs):
        '''Hook for the code you want to run whenever the effect is triggered. Required.'''
        pass

    def on_tick(self, *args, **kwargs):
        '''Hook for actions that occur per-tick, a designer-set sub-duration.'''
        pass

class Mod():
    '''A single stat mod object. One buff or trait can hold multiple mods, for the same or different stats.'''
    
    stat = 'null'       # The stat string that is checked to see if this mod should be applied  
    base = 0            # Buff's value
    perstack = 0        # How much additional value is added to the buff per stack
    modifier = 'add'    # The modifier the buff applies. 'add' or 'mult' 

    def __init__(self, stat: str, modifier: str, base, perstack=0) -> None:
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
    '''The handler for buffs. Assigned as a property to buffable game objects.
    
    Attributes:
        obj:        The game object this handler is attached to
        dbkey:      The desired key for the attribute used as the buff dictionary
    
    Properties:
        db:         The buff dictionary on the game object
        traits:     All "trait buffs"; buffs with passive modifiers
        effects:    All "effect buffs"; buffs with trigger conditions

    Getters:
        get:            Finds a buff with the specified key on the object; returns a single instance object or None
        get_by_type:    Finds all buffs that match the type; returns dict of {key: instance} or None
        get_by_stat:    Finds all buffs with a mod that affects the stat; returns dict of {key: instance} or None

    Methods:
        add:        Adds the specified buff. Has numerous optional arguments
        remove:     Removes the specified buff. Requires the buff's "key"
        cleanup:    Checks for expired buffs and cleans them up
        view:       Returns a string of buff names and flavor text
        check:      Modifies a given number by all buffs/perks with the specified string
        find:       True if specified buff is on object; false if not
        trigger:    Triggers the effects of all buffs/perks with the specified string'''

    obj = None
    dbkey = "buffs"
    
    def __init__(self, obj):
        self.obj = obj
        if not self.obj.attributes.has(self.dbkey): self.obj.attributes.add(self.dbkey, {})

    def __getattr__(self, __name: str) -> BaseBuff:
       return self.get(__name)

    #region properties
    @property
    def db(self):
        '''The object attribute we use for the buff database. Convenience shortcut (equal to self.obj.db.dbkey)'''
        return self.obj.attributes.get(self.dbkey)

    @property
    def traits(self):
        '''All buffs on this handler that modify a stat.'''
        _t = {k:self.get(k) for k,v in self.db.items() if v['ref'].mods}
        return _t

    @property
    def effects(self):
        '''All buffs on this handler that trigger off an event.'''
        _e = {k:self.get(k) for k,v in self.db.items() if v['ref'].trigger}
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
    #endregion
    
    #region methods
    def add(self, buff: BaseBuff,
        key: str=None, source = None, stacks = 1, duration = None, 
        context={}, *args, **kwargs
        ):
        
        '''Add a buff or effect instance to this object, respecting all stacking/refresh/reapplication rules.
        
        Args:
            buff:       The buff class you wish to add
            source:     (optional) The source of this buff.
            stacks:     (optional) The number of stacks you want to add, if the buff is stacking
            duration:   (optional) The amount of time, in seconds, you want the buff to last.
            context:    (optional) An existing context you want to add buff details to
        
        Returns the buff context for the action.
        '''
        
        _context = context

        # Create the buff dict that holds a reference and all runtime information.
        b = { 
            'ref': buff,
            'pid': None, 
            'start': time.time(),
            'duration': duration, 
            'prevtick': None,
            'paused': False, 
            'stacks': stacks,  
            'source': source }

        # Generate the pID (procedural ID) from the object's dbref (uID) and buff key. 
        # This is the actual key the buff uses on the dictionary
        pid = key
        if not pid:
            uid = str(source.dbref).replace("#","")
            pid = buff.key if buff.unique is True else buff.key + uid
        

        # If the buff is on the dictionary, we edit existing values for refreshing/stacking
        if pid in self.db.keys(): 
            b = dict( self.db[pid] )
            if buff.refresh: b['start'] = time.time()
            if buff.stacking: b['stacks'] = min( b['stacks'] + stacks, buff.maxstacks )
        
        # Setting duration, initial tick, and uid, if relevant
        b['prevtick'] = time.time() if buff.ticking else None
        b['duration'] = duration if duration else buff.duration
        b['pid'] = pid

        # Apply the buff!
        self.db[pid] = b

        # Create the buff instance and run the on-application hook method
        instance: BaseBuff = buff(self.obj, self, pid, b)
        instance.on_apply(**_context)
        if buff.ticking: tick_buff(self.obj, self, pid, _context)
        
        # Clean up the buff at the end of its duration through a delayed cleanup call
        utils.delay( b['duration'] + 0.01, cleanup_buffs, self, persistent=True )

        # Apply the buff and pass the Context upwards.
        return _context

    def remove(self, key, 
        dispel=False, expire=False, loud=True, 
        context={}, *args, **kwargs
        ):
        '''Remove a buff or effect with matching key from this object. Calls on_remove, on_dispel, or on_expire, depending on arguments.
        
        Args:
            key:    The buff key
            dispel: Calls on_dispel when True
            expire: Calls on_expire when True. Used when cleaned up.
            loud:  Calls on_remove when True. Default remove hook.'''

        if key not in self.db: return None
        
        _context = context
        buff: BaseBuff = self.db[key]['ref']
        instance : BaseBuff = buff(self.obj, self, key, self.db[key])
        
        if loud:
            if dispel: instance.on_dispel(**context)
            elif expire: instance.on_expire(**context)

            instance.on_remove(**context)

        del instance
        del self.db[key]

        return _context

    def get(self, buff: str):
        '''If the specified key is on this handler, return the instanced buff. Otherwise return None.
        You should delete this when you're done with it, so that garbage collection doesn't have to.'''
        _return = None
        _b = self.db.get(buff)
        if _b: _return = _b["ref"](self.obj, self, buff, _b)
        return _return

    def get_by_type(self, buff:BaseBuff):
        '''Returns a dictionary of instanced buffs of the specified type in the format {pid: instance}.'''
        return {k: self.get(k) for k,v in self.db.items() if v['ref'] == buff}

    def get_by_stat(self, stat:str):
        '''Returns a dictionary of instanced buffs which modify the specified stat in the format {pid: instance}.'''
        _cache = self.traits
        if not _cache: return None

        buffs = {k:buff 
                for k,buff in _cache.items() 
                for m in buff.mods 
                if not buff.paused
                if buff.conditional()
                if m.stat == stat}
        return buffs

    def check(self, base: float, stat: str, loud=True, context={}):    
        '''Finds all buffs and perks related to a stat and applies their effects.
        
        Args:
            base: The base value you intend to modify
            stat: The string that designates which stat buffs you want
            
        Returns the base value modified by relevant buffs, and any messaging.'''
        # Buff cleanup to make sure all buffs are valid before processing
        self.cleanup()

        # Find all buffs and traits related to the specified stat.
        applied = self.get_by_stat(stat)
        if not applied: return base

        # The final result
        final = self._calculate_mods(base, stat, applied)

        # Run the "after check" functions on all relevant buffs
        for buff in applied.values():
            buff: BaseBuff
            if loud: buff.after_check(**context)
            del buff
        return final
 
    def get_by_trigger(self, trigger:str):
        '''Returns a dictionary of instanced buffs which fire off the designated trigger, in the format {pid: instance}'''
        _cache = self.effects
        return {k: self.get(k) 
            for k,v in _cache.items() 
            if v['ref'].trigger == trigger 
            if not v.get('paused')}
    
    def trigger(self, trigger: str, context:dict = {}):
        '''Activates all perks and effects on the origin that have the same trigger string. 
        Takes a trigger string and a dictionary that is passed to the buff as kwargs.
        '''
        self.cleanup()
        _effects = self.effects
        if _effects is None: return None

        # Trigger all buffs whose trigger matches the trigger string
        for buff in _effects.values():
            buff: BaseBuff
            if buff.trigger == trigger and not buff.paused:
                buff.on_trigger(**context)
    
    def pause(self, key: str):
        """Pauses the buff. This excludes it from being checked for mods, triggered, or cleaned up. Used to make buffs 'playtime' instead of 'realtime'."""
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
    def _calculate_mods(self, base, stat:str, buffs:dict):
        '''Calculates a return value based on a list of packed mods (mod + stacks) and a base.'''
        if not buffs: return base
        add = 0
        mult = 0

        for buff in buffs.values():
            for mod in buff.mods:
                if mod.stat == stat:    
                    if mod.modifier == 'add':   add += mod.base + ( (buff.stacks - 1) * mod.perstack)
                    if mod.modifier == 'mult':  mult += mod.base + ( (buff.stacks - 1) * mod.perstack)
        
        final = (base + add) * (1.0 + mult)
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

def tick_buff(obj, handler: BuffHandler, pid: str, context={}, initial=True):
    '''Ticks a buff. If a buff's ticking value is True, this is called when the buff is applied, and then once per tick cycle.'''
    # Cache a reference and find the buff on the object
    _cache = handler.db
    if pid not in _cache.keys(): return
    b = dict(_cache[pid])

    # Instantiate the buff and tickrate
    buff: BaseBuff = b['ref'](obj, handler, pid, b)
    tr = buff.tickrate
    
    if tr > time.time() - buff.prevtick and initial is not True: return     # This stops the old ticking process if you refresh/stack the buff
    
    # If the duration has run out, tick one last time, then stop this process
    if buff.duration < time.time() - buff.start:
        if tr < time.time() - buff.prevtick: buff.on_tick(**context)
        return

    # If it's time, call the buff's on_tick method and update prevtick
    if tr < time.time() - buff.prevtick: buff.on_tick(**context)
    
    _cache[pid]['prevtick'] = time.time()

    # Recur this function at the tickrate interval, if it didn't stop/fail
    utils.delay(tr, tick_buff, obj=obj, handler=handler, pid=pid, context=context, initial=False)