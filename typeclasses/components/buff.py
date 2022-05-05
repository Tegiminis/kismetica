import time
import random
from evennia import utils, TICKER_HANDLER
from typeclasses.objects import DefaultObject as Object
from typeclasses.context import Context

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
        return self._owner

    def __init__(self, owner, data: dict, context: dict = None) -> None:
        self._owner = owner
        self.data = data
        _keys = data.keys()
        self.pid = self.key + data['uid'] if 'uid' in _keys and data['uid'] is not None else self.key
        if 'start' in _keys: self.start = self.data['start']
        if 'stacks' in _keys: self.stacks = self.data['stacks']
        if 'duration' in _keys: self.duration = self.data['duration']
        if 'prevtick' in _keys: self.prevTick = self.data['prevtick']
        if 'source' in _keys: self.source = self.data['prevtick']

        self.context = context

    def on_apply(self):
        '''Hook function to run when this buff is applied to an object.'''
        pass
    
    def on_remove(self):
        '''Hook function to run when this buff is removed from an object.'''
        pass

    def on_remove_stack(self):
        '''Hook function to run when this buff loses stacks.'''
        pass

    def on_dispel(self):
        '''Hook function to run when this buff is dispelled from an object (removed by someone other than the buff holder).'''
        pass

    def on_expire(self):
        '''Hook function to run when this buff expires from an object.'''
        pass

    def after_check(self):
        '''Hook function to run after this buff's mods are checked.'''
        pass

    def on_trigger(self):
        '''Hook for the code you want to run whenever the effect is triggered. Required.'''
        pass

    def on_release(self):
        '''Hook for the code you want to run whenever the effect is released (reverse of trigger). Optional.'''
        pass

    def on_tick(self):
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

    #region properties
    @property
    def db(self):
        '''The attribute we use for the buff database. Convenience shortcut (equal to self.obj.db.buffs)'''
        return self.obj.db.buffs

    @property
    def traits(self):
        _buffs = [x for x in self.db.values() if x['ref'].mods]
        return _buffs

    @property
    def effects(self):
        _buffs = [x for x in self.db.values() if x['ref'].trigger]
        return _buffs

    @property
    def playtime_buffs(self):
        _buffs = [x for x in self.db.values() if x['ref'].playtime]
        return _buffs
    #endregion
    
    #region methods
    def add(
        self,
        buff: Buff,
        source = None, 
        stacks = 1, 
        duration = None, 
        context: dict = None
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

        
        _ref: Buff = buff  
        _context = context if context else None

        # Create the buff dict that holds a reference and all runtime information.
        b = { 
            'ref': _ref,
            'uid': None, 
            'start': time.time(),
            'duration': duration, 
            'prevtick': None, 
            'stacks': stacks,  
            'source': source }

        # Generate the pID (procedural ID) from the object name (uID) and buff key. 
        # This is the actual key the buff uses on the dictionary
        uid = str(source)
        pid = _ref.key if _ref.unique is True else _ref.key + uid

        # If the buff is on the dictionary, we edit existing values for refreshing/stacking
        if pid in self.db.keys(): 
            b = dict( self.db[pid] )
            if _ref.refresh: b['start'] = time.time()
            if _ref.stacking: b['stacks'] = min( b['stacks'] + stacks, _ref.maxstacks )
        
        # Setting duration, initial tick, and uid, if relevant
        b['prevtick'] = time.time() if _ref.ticking else None
        b['duration'] = duration if duration else _ref.duration
        b['uid'] = uid if _ref.unique is False else None

        # Apply the buff!
        self.db[pid] = b

        # Create the buff instance and run the on-application hook method
        instance: Buff = _ref(self.obj, b, _context)
        instance.on_apply()

        # del instance
        # self.obj.location.msg("   |rBreakpoint: |nClean cache")

        if _ref.ticking:
            # utils.delay(_tr, tick_buff, persistent=True, buff=buff, context=context)
            # self.obj.location.msg("   |rBreakpoint: |nStart ticking")
            tick_buff(b, _context)
        
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
        delay=0
        ):
        '''Remove a buff or effect with matching key from this object. Calls on_remove, on_dispel, or on_expire, depending on arguments.
        
        Args:
            key:     The buff key
            dispel: Call on_dispel when True.
            expire: Call on_expire when True.
            quiet:  Do not call on_remove when True.'''

        if key not in self.db: return None
    
        buff: Buff = self.db[key]['ref']
        instance : Buff = buff(self.obj)
        
        origin = source if source is not None else self.obj
        context = Context(origin, self.obj, buff=self.db[key])
        
        if not quiet:
            if dispel: 
                instance.on_dispel(context)
            elif expire: 
                instance.on_expire(context)

            instance.on_remove(context)


        del instance
        del self.db[key]

        return context

    def cleanup(self):
        '''Cleans up all old buffs on this object'''
        cleanup_buffs(self.obj)

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

    def check(self, base: float, stat: str, quiet = False):    
        '''Finds all buffs and perks related to a stat and applies their effects.
        
        Args:
            base: The base value you intend to modify
            stat: The string that designates which stat buffs you want
            
        Returns the base value modified by relevant buffs, and any messaging.'''

        # Buff cleanup to make sure all buffs are valid before processing
        self.cleanup()

        # Find all buffs and traits related to the specified stat.
        _toApply: tuple = self._collect_mods(stat)
        # if _toApply:  obj.location.msg('Mods collected: ' + str(_toApply))

        if not _toApply: return base

        # The final result
        final = self._calc_packed_mods(_toApply[1], base)

        # Run the "after check" functions on all relevant buffs
        for buff in _toApply[0]:
            # if 'origin' in buff.keys(): buff['origin'].location.msg('Debug Checking buff of type: ' + stat)
            instance = buff['ref'](self.obj)
            _handler = self.db if isinstance(instance, Buff) else self.obj.db.perks 
            context = Context(self.obj, self.obj, buff=buff)
            if not quiet: instance.after_check(context)
            del instance

        return final
    
    def find(self, buff: BaseBuff):
        '''Finds the specified buff on this object, if it exists. Returns a boolean.'''
        for b in self.db:
            if b['ref'] == buff: return True
        return False
 
    def trigger(self, trigger: str, 
        source=None, target=None, context:dict = None
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
            if x['ref'].trigger == trigger and x['paused'] is not True:
                toActivate.append(x)
        
        # Go through and trigger all relevant perks and effects, passing their trigger messages upwards.
        for x in toActivate:
            # target.location.msg("Debug Triggered Perk/Buff: " + str(x) )
            _eff : BaseBuff = x['ref']
            instance : BaseBuff = _eff(self.obj)

            if _context: _context.buff = x
            else: 
                origin = source if source is not None else self.obj
                target = target if target is not None else self.obj

                _context = Context(origin, target, buff=x)
            
            instance.on_trigger(_context)
            del instance
    
    def pause(self, key: str):
        """Pauses the buff. This excludes it from being checked for mods, triggered, or cleaned up. Used to make buffs 'playtime' instead of 'realtime'."""
        if key in self.db.values():
            # Mark the buff as paused
            buff = self.db[key]
            buff['paused'] = True

            # Figure out our new duration
            t = time.time()         # Time
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
            # Mark the buff as paused
            buff = self.db[key]
            buff['paused'] = False

            # Start our new timer
            buff['start'] = time.time()
            utils.delay( buff['duration'] + 0.01, cleanup_buffs, self.obj, persistent=True )
        return

    #region private methods
    def _collect_mods(self, stat: str):
        '''Collects a list of all mods affecting the specified stat on buffs affect this object.
        Vars:
            stat:       The string to search for in the Mods on buffs'''
        _cache = self.obj.traits
        if not _cache: return None
        
        mods = []
        buffs = []

        for buff in _cache:
            ref = buff['ref']

            for m in ref.mods:
                if buff['paused'] is True: break
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

    #region properties
    @property
    def db(self):
        return self.obj.db.perks

    @property
    def traits(self):
        _perks = [x for x in self.obj.db.perks.values() if x['ref'].mods ]
        return _perks

    @property
    def effects(self):
        _perks = [x for x in self.obj.db.perks.values() if x['ref'].trigger ]
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

    def remove(self, key, source=None):
        '''Removes a perk with matching key or slot from the object's handler. Calls the perk's on_remove function.'''
        origin = source if source is not None else self.obj
        if key in self.db.keys():
            perk = self.db[key]['ref']
            context = Context(origin, self.obj, buff=perk, handler=self.db)

            instance: Perk = perk()
            instance.on_remove(context)
            del self.db[key]
            del instance
            
            return context
        else: return None
    #endregion

def cleanup_buffs(obj):
    '''Cleans up all buffs on that object. Removes any buffs which have an expired timer'''
    _buffs = dict(obj.db.buffs)
    
    if _buffs:
        # Dict comprehension to find buffs for removal
        remove = [ k 
            for k,v in _buffs.items() 
            if v['duration'] < time.time() - v['start']
            if v['paused'] is not True]

        # obj.location.msg("Debug: Cleaning up buffs | %s" % str(remove))
        
        # Remove all buffs in the list
        for k in remove: 
            obj.buffs.remove(k, expire=True)

def tick_buff(buff: dict, context: Context, initial=True):
    '''Ticks a buff. If a buff's ticking value is True, this is called when the buff is applied, and then once per tick cycle.'''
    # Cache a reference and find the buff on the object
    _buffs = context.target.db.buffs
    if context.buffKey in _buffs.keys(): 
        context.buff = _buffs[context.buffKey]
        buff = _buffs[context.buffKey]

    # Instantiate the buff and tickrate
    ref: BaseBuff = buff['ref'](context.target)
    _tr = ref.tickrate

    # This stops the old ticking process if you refresh/stack the buff
    if _tr > time.time() - context.buffPrevTick and initial is not True: 
        return
    
    # If the duration has run out, tick one last time, then stop this process
    if context.buffDuration < time.time() - context.buffStart:
        if _tr < time.time() - context.buffPrevTick: ref.on_tick(context)
        return
    
    # If the buff has since been removed, stop this process
    if context.buffKey not in _buffs.keys(): 
        return

    # If it's time, call the buff's on_tick method and update prevtick
    if _tr < time.time() - context.buffPrevTick: 
        ref.on_tick(context)
    
    buff['prevtick'] = time.time()

    # Recur this function at the tickrate interval, if it didn't stop/fail
    utils.delay(_tr, tick_buff, buff=context.buff, context=context, initial=False)