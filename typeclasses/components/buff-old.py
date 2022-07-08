import time
import random
from evennia import utils, TICKER_HANDLER
from typeclasses.objects import DefaultObject as Object
from evennia.typeclasses.attributes import AttributeProperty

class BaseBuff():
    '''Base class for all "buffs" in the game. Buffs are permanent and temporary modifications to stats, and trigger conditions that run arbitrary code.

    Strings:
        key:         The buff's unique key. Will be used as the buff's key in the handler
        name:       The buff's name. Used for user messaging
        flavor:     The buff's flavor text. Used for user messaging
        trigger:    The buff's trigger string. Used for effects
        release:    The buff's release string. Used for effects
    '''
    
    key = 'template'             # The buff's unique key. Will be used as the buff's key in the handler
    name = 'Template'           # The buff's name. Used for user messaging
    flavor = 'Template'         # The buff's flavor text. Used for user messaging
    isVisible = True            # If the buff is considered "visible"; it shows up to the player

    trigger = None        # The effect's trigger string, used for functions
    release = None        # The effect's release string, used for functions

    trigger_msg = None

    cooldown = 0

    mods = None

    _owner = None

    @property
    def owner(self):
        '''Returns the object this buff is applied to.'''
        return self._owner

    def __init__(self, owner, pid, data: dict) -> None:
        self._owner = owner
        self.pid = pid
        self.start = data.get('start')
        self.stacks = data.get('stacks')
        self.duration = data.get('duration')
        self.prevTick = data.get('prevtick')
        self.source = data.get('source')

    def remove(self, source=None, dispel=False, expire=False, quiet=False, delay=0, context={}):
        '''Helper method which removes this buff from its handler.'''
        self.owner.buffs.remove(self.pid, source, dispel, expire, quiet, delay, context)

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

    def on_release(self, *args, **kwargs):
        '''Hook for the code you want to run whenever the effect is released (reverse of trigger). Optional.'''
        pass

    def on_tick(self, *args, **kwargs):
        '''Hook for actions that occur per-tick, a designer-set sub-duration.'''
        pass

class Buff(BaseBuff):
    '''A buff is comprised of one or more temporary stat modifications or trigger effects. Includes a duration, stack size, and so on.

    Strings:
        key:        The buff's unique key. Will be used as the buff's key in the handler
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
    unique = False              # Does the buff overwrite existing buffs with the same key on the same target?
    maxstacks = 1               # The maximum number of stacks the buff can have.

    ticking = False
    tickrate = 5

    def ticknum(self, start):
        x = (time.time() - start) / self.tickrate
        return int(x)

class Perk(BaseBuff):
    '''A permanent buff. Uses "slot" for the key in the dict.
    
    Strings:
        key:         The perk's unique key. Will be used as the perk's key in the handler
        name:       The perk's name. Used for user messaging
        flavor:     The perk's flavor text. Used for user messaging
    Vars:
        slot:       If defined, uses this for the perk's dictionary key. Otherwise, uses the perk key.
        trigger:    Trigger string, used to activate it through the perk handler.
        release:    Release string, currently unused.
    Funcs:
        on_trigger: Hook for code to run when the perk is triggered. Required.
        on_release: Hook for code to run when the perk is released.
    '''

    slot = None

    def remove(self, source=None, context={}):
        '''Helper method which removes this buff from its handler.'''
        self.owner.perks.remove(self.key, source, context)

class Mod():
    '''A single stat modification. One buff or trait can hold multiple mods, for the same or different stats.'''
    
    stat = 'null'             # The stat the buff affects. Essentially a tag used to find the buff for coding purposes  
    base = 0                    # Buff's value
    perstack = 0                # How much additional value is added to the buff per stack
    modifier = 'add'            # The modifier the buff applies. 'add' or 'mult' 

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
    
    Properties:
        obj:        The game object this handler is attached to
        db:         The buff dictionary on the game object
        traits:     All "trait buffs"; buffs with passive modifiers
        effects:    All "effect buffs"; buffs with trigger conditions


    Methods:
        add:        Adds the specified buff. Has numerous optional arguments
        remove:     Removes the specified buff. Requires the buff's "key"
        cleanup:    Checks for expired buffs and cleans them up
        view:       Returns a string of buff names and flavor text
        check:      Modifies a given number by all buffs/perks with the specified string
        find:       True if specified buff is on object; false if not
        trigger:    Triggers the effects of all buffs/perks with the specified string'''

    obj = None
    
    def __init__(self, obj):
        self.obj = obj
        if not self.obj.attributes.has('buffs'): self.obj.db.buffs = {}

    def __getattr__(self, __name: str) -> BaseBuff:
       return self.get(__name)

    #region properties
    @property
    def db(self):
        '''The attribute we use for the buff database. Convenience shortcut (equal to self.obj.db.buffs)'''
        return self.obj.db.buffs

    @property
    def traits(self):
        _buffs = {k:v for k,v in self.db.items() if v['ref'].mods}
        return _buffs

    @property
    def effects(self):
        _buffs = {k:v for k,v in self.db.items() if v['ref'].trigger}
        return _buffs

    @property
    def playtime_buffs(self):
        _buffs = {k:v for k,v in self.db.items() if v['ref'].playtime}
        return _buffs
    #endregion
    
    #region methods
    def add(
        self,
        buff: Buff,
        key: str = None,
        source = None, 
        stacks = 1, 
        duration = None, 
        context: dict = {}
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
            'stacks': stacks,  
            'source': source }

        # Generate the pID (procedural ID) from the object name (uID) and buff key. 
        # This is the actual key the buff uses on the dictionary
        pid = key
        if not pid:
            uid = str(source.dbref).replace("#","") if source else str(source)
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
        instance: Buff = buff(self.obj, pid, b)
        instance.on_apply(**_context)

        # del instance
        # self.obj.location.msg("   |rBreakpoint: |nClean cache")

        if buff.ticking: tick_buff(self.obj, pid, _context)
        
        # Clean up the buff at the end of its duration through a delayed cleanup call
        utils.delay( b['duration'] + 0.01, cleanup_buffs, self.obj, persistent=True )

        # Apply the buff and pass the Context upwards.
        return _context

    def remove(
        self, 
        key,
        source=None, 
        dispel=False, 
        expire=False, 
        quiet=False, 
        delay=0,
        context={}
        ):
        '''Remove a buff or effect with matching key from this object. Calls on_remove, on_dispel, or on_expire, depending on arguments.
        
        Args:
            key:     The buff key
            dispel: Call on_dispel when True.
            expire: Call on_expire when True.
            quiet:  Do not call on_remove when True.'''

        if key not in self.db: return None
    
        buff: Buff = self.db[key]['ref']
        instance : Buff = buff(self.obj, key, self.db[key])
        
        origin = source if source is not None else self.obj
        
        if not quiet:
            if dispel: 
                instance.on_dispel(**context)
            elif expire: 
                instance.on_expire(**context)

            instance.on_remove(**context)

        del instance
        del self.db[key]

    def cleanup(self):
        '''Cleans up all old buffs on this object'''
        cleanup_buffs(self.obj)

    def get(self, buff: str):
        '''If the specified key is on this handler, return the instanced buff. Otherwise return None.
        You should delete this when you're done with it, so that garbage collection doesn't have to.'''
        cleanup_buffs(self.obj)
        _return = None
        _b = self.db.get(buff)
        if _b: _return = _b["ref"](self.obj, buff, _b)
        return _return

    def get_by_type(self, buff:BaseBuff):
        '''Returns a dictionary of instanced buffs of the specified type in the format {pid: instance}.'''
        return {k: self.get(k) for k,v in self.db.items() if v['ref'] == buff}
    
    def view(self) -> list:
        '''Gets the name and flavor of all buffs and effects on the object.'''
        self.cleanup()
        message = []
        
        if self.db:
            _cache = self.db.values()
            for x in _cache:
                buff: Buff = x.get('ref')
                msg = "    " + buff.name + ": " + buff.flavor
                message.append(msg)
        
        return message

    def get_by_stat(self, stat:str):
        '''Returns a dictionary of instanced buffs which modify the specified stat in the format {pid: instance}.'''
        _cache = self.obj.traits
        if not _cache: return None

        buffs = {}

        for key, buff in _cache.items():
            instance: BaseBuff = buff['ref'](self.obj, key, buff)
            for m in instance.mods:
                if buff.get('paused') is True: break
                if not instance.conditional(): break
                if m.stat == stat:
                    buffs[key] = instance
        return buffs

    def check(self, base: float, stat: str, quiet = False, context={}):    
        '''Finds all buffs and perks related to a stat and applies their effects.
        
        Args:
            base: The base value you intend to modify
            stat: The string that designates which stat buffs you want
            
        Returns the base value modified by relevant buffs, and any messaging.'''
        _start = time.time()
        # Buff cleanup to make sure all buffs are valid before processing
        self.cleanup()

        # Find all buffs and traits related to the specified stat.
        applied = self.get_by_stat(stat)
        if not applied: return base

        # The final result
        final = self._calculate_mods(base, stat, applied)

        # Run the "after check" functions on all relevant buffs
        for buff in applied.values():
            # if 'origin' in buff.keys(): buff['origin'].location.msg('Debug Checking buff of type: ' + stat)
            buff: BaseBuff
            if not quiet: buff.after_check(**context)
            del buff
        _end = time.time()
        print(_end - _start)
        return final
 
    def get_by_trigger(self, trigger:str):
        '''Returns a dictionary of instanced buffs which fire off the designated trigger, in the format {pid: instance}'''
        _cache = self.obj.effects
        return {k: self.get(k) 
            for k,v in _cache.items() 
            if v['ref'].trigger == trigger 
            if not v.get('paused')}
    
    def trigger(self, trigger: str, 
        source=None, target=None, context:dict = {}
        ) -> str:
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
            if x['ref'].trigger == trigger and x.get('paused') is not True:
                toActivate.append(x)
        
        # Go through and trigger all relevant perks and effects, passing their trigger messages upwards.
        for x in toActivate:
            # target.location.msg("Debug Triggered Perk/Buff: " + str(x) )
            _eff : BaseBuff = x['ref']
            instance : BaseBuff = _eff(self.obj, x)
            
            instance.on_trigger(**context)
            del instance
    
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
            utils.delay( buff['duration'] + 0.01, cleanup_buffs, self.obj, persistent=True )
        return

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

class PerkHandler(object):
    '''The handler for perks. Assigned as a property to perkable game objects.

    You should use the buffhandler (obj.buffs) to .check traits and .trigger
    effects. The perk handler is purely to add/remove perks, as perks are
    "more permanent" buffs.
    
    Properties:
        obj:        The game object this handler is attached to
        db:         The buff dictionary on the game object
        traits:     All "trait perks"; perks with passive modifiers
        effects:    All "effect perks"; perks with trigger conditions

    Methods:
        add:    Adds a perk to the object
        remove: Removes a perk from the object
    '''

    obj = None
    
    def __init__(self, obj):
        self.obj = obj
        if not self.obj.attributes.has('perks'): self.obj.db.perks = {}

    def __getattr__(self, __name: str) -> BaseBuff:
       return self.get(__name)

    #region properties
    @property
    def db(self):
        return self.obj.db.perks

    @property
    def traits(self):
        _perks = {k:v for k,v in self.db.items() if v['ref'].mods}
        return _perks

    @property
    def effects(self):
        _perks = {k:v for k,v in self.db.items() if v['ref'].trigger}
        return _perks
    #endregion

    #region methods
    def add(self: Object, perk: Perk, slot: str = None):
        '''Adds the referenced perk or trait to the object.'''
        if perk is None: return
        
        b = { 'ref': perk }     
        
        if slot: self.db[slot] = b
        elif perk.slot: self.db[perk.slot] = b
        else: self.db[perk.key] = b     

    def remove(self, key, source=None, context={}):
        '''Removes a perk with matching key or slot from the object's handler. Calls the perk's on_remove function.'''
        if key in self.db.keys():
            perk = self.db[key]['ref']
            instance: Perk = perk(self.obj, self.db[key])
            instance.on_remove(**context)
            del self.db[key]
            del instance
        else: return None

    def get(self, buff: str):
        '''If the specified key is on this handler, return the instanced buff. Otherwise return None.
        You should delete this when you're done with it, so that garbage collection doesn't have to.'''
        _return = None
        _b = self.db.get(buff)
        if _b: _return = _b["ref"](self.obj, buff, _b)
        return _return

    def get_by_type(self, perk:BaseBuff):
        '''Instances all buffs of the specified type and returns a list of the instances.'''
        return {k: self.get(k) for k,v in self.db.items() if v == perk }
    #endregion

class BuffableProperty(AttributeProperty):
    
    def at_get(self, value, obj):
        _value = obj.buffs.check(value, self._key)
        return _value

def cleanup_buffs(obj):
    '''Cleans up all buffs on that object. Removes any buffs which have an expired timer'''
    _buffs = dict(obj.db.buffs)
    
    if _buffs:
        # Dict comprehension to find buffs for removal
        remove = [ k 
            for k,v in _buffs.items()
            if v['duration'] > 0 
            if v['duration'] < time.time() - v['start']
            if v.get('paused') is not True]

        # obj.location.msg("Debug: Cleaning up buffs | %s" % str(remove))
        
        # Remove all buffs in the list
        for k in remove: 
            obj.buffs.remove(k, expire=True)

def tick_buff(obj, pid: str, context: dict, initial=True):
    '''Ticks a buff. If a buff's ticking value is True, this is called when the buff is applied, and then once per tick cycle.'''
    # Cache a reference and find the buff on the object
    _buffs = obj.buffs.db
    if pid not in _buffs.keys(): return

    b = dict(_buffs[pid])

    # Instantiate the buff and tickrate
    ref = b['ref']
    buff: Buff = ref(obj, b)
    _tr = buff.tickrate
    
    if _tr > time.time() - buff.prevTick and initial is not True: return     # This stops the old ticking process if you refresh/stack the buff
    
    # If the duration has run out, tick one last time, then stop this process
    if buff.duration < time.time() - buff.start:
        if _tr < time.time() - buff.prevTick: buff.on_tick()
        return

    # If it's time, call the buff's on_tick method and update prevtick
    if _tr < time.time() - buff.prevTick: buff.on_tick()
    
    _buffs[pid]['prevtick'] = time.time()

    # Recur this function at the tickrate interval, if it didn't stop/fail
    utils.delay(_tr, tick_buff, obj=obj, pid=pid, context=context, initial=False)