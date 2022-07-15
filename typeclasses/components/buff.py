"""Buffs - Tegiminis 2022

A buff is a timed object, attached to a game entity, that modifies values, triggers 
code, or both. It is a common design pattern in RPGs, particularly action games.

This contrib gives you a buff handler to apply to your objects, a buff class to extend them,
and a sample property class to show how to automatically check modifiers.

## Quick Start
Assign the handler to a property on the object, like so.

```python
@lazy_property
def buffs(self) -> BuffHandler:
    return BuffHandler(self)```

You may then call the handler to add or manipulate buffs.

### Customization

If you want to customize the handler, you can feed the constructor two arguments:
- `dbkey`: The string you wish to use as a key for the buff database. Defaults to "buffs". This allows you to keep separate buff pools - for example, "buffs" and "perks".
- `autopause`: If you want this handler to automatically pause certain buffs when its owning object is unpuppeted.

> IMPORTANT: If you enable autopausing, you MUST initialize the property in your object's
> `at_init` hook to cache. Otherwise, a hot reload can cause playtime buffs to not update properly
> on puppet/unpuppet. You have been warned!

Let's say you want another handler for an object, `perks`, which has a separate database and 
respects playtime buffs. You'd assign this new property as so:

```python
    @lazy_property
    def perks(self) -> BuffHandler:
        return BuffHandler(self, dbkey='perks', autopause=True)
```

And add `self.perks` to the object's `at_init`.

### Using the Handler

To actually make use of the handler, you still have to do some leg work.

#### Apply a Buff

Call the handler `add(BuffClass)` method. This requires a class reference, and also contains a number of 
optional arguments to customize the buff's duration, stacks, and so on. You can also store any arbitrary value 
in the buff's cache by passing a dictionary through the `to_cache` argument. This will not overwrite the normal
values on the cache.

```python
self.buffs.handler.add(StrengthBuff)    # A single stack of StrengthBuff with normal duration
self.buffs.handler.add(DexBuff, stacks=3, duration=60)  # Three stacks of DexBuff, with a duration of 60 seconds
self.buffs.handler.add(ReflectBuff, to_cache={'reflect': 0.5})  # A single stack of ReflectBuff, with an extra cache value
```

Two important attributes on the buff are checked when the buff is applied: `refresh` and `unique`.
- `refresh` (default: True) determines if a buff's timer is refreshed when it is reapplied.
- `unique` determines if the buff uses the buff's normal key (True) or one created with the key and the applier's dbref (False)

#### Modify

Call the handler `check(value, stat)` method wherever you want to see the modified value. 
This will return the value, modified by and relevant buffs on the handler's owner (identified by 
the `stat` string).

For example, let's say you want to modify how much damage you take. That might look something like this

```python
# The method we call to damage ourselves
def take_damage(self, source, damage):
    _damage = self.buffs.check(damage, 'taken_damage')
    self.db.health -= _damage
```

#### Trigger

Call the handler `trigger(triggerstring)` method wherever you want an event call. This 
will call the `at_trigger` hook method on all buffs with the relevant trigger.

For example, let's say you want to trigger a buff to "detonate" when you hit your target with an attack.
You'd write a buff with at least the following stats:

```python
triggers = ['take_damage']
def at_trigger(self, trigger, *args, **kwargs)
    self.owner.take_damage(100)
```

And then call `handler.trigger('take_damage')` in the method you use to take damage.

#### Tick

Ticking buffs are slightly special. They are similar to trigger buffs in that they run code, but instead of
doing so on an event trigger, they do so are a periodic tick. A common use case for a buff like this is a poison,
or a heal over time.

All you need to do to make a buff tick is ensure the `tickrate` is 1 or higher, and it has code in its `at_tick`
method. Once you add it to the handler, it starts ticking!

## Buffs

But wait! You still have to actually create the buffs you're going to be applying.

Creating a buff is very easy: extend BaseBuff into a new class, and fill in all the relevant buff details.
However, there are a lot of individual moving parts to a buff! Here's a step-through of the important stuff.

### Basics

Regardless of any mods or hook methods, all buffs have the following qualities:

- They have customizable `key`, `name`, and `flavor` strings.
- They can stack, if `maxstacks` is not equal to 1. If it's 0, the buff stacks forever. 
- They have a `duration`, and automatically clean up at the end of it (-1 for infinite duration, 0 to cleanup immediately).

### Modifiers

Buffs which have one or more Mod objects in them can modify stats. You can use the handler method to check all 
mods of a specific stat string and apply their modifications to the value; however, you are encouraged to use 
`check` in a getter/setter, for easy access.

Mod objects consist of only four values, assigned by the constructor in this order:

- `stat`: The stat you want to modify. When `check` is called, this string is used to find all the mods that are to be collected.
- `mod`: The modifier. Defaults are 'add' and 'mult'. Modifiers are calculated additively, and in standard arithmetic order (see `_calculate_mods` for more)
- `value`: How much value the modifier gives regardless of stacks
- `perstack`: How much value the modifier grants per stack, INCLUDING the first. (defualt: 0)

To add a mod to a buff, you do so in the buff definition, like this:
```
def DamageBuff(BaseBuff):
    mods = [Mod('damage', 'add', 10)]
```

No mods applied to the value are permanent in any way. All calculations are done at
runtime, and the mod values are never stored anywhere except on the buff in question. In
other words: you don't need to track the origin of particular stat mods, and you
will never permanently change a stat modified by a trait buff. To remove the modification, simply
remove the buff off the object.

### Triggers

Buffs which have one or more strings in the `triggers` attribute can be triggered by events.

When the handler `trigger` method is called, it searches all buffs on the handler for any with a matching
trigger, then calls their `at_trigger` methods. You can tell which trigger is the one it fired with by the `trigger`
argument in the method.

``` 
def AmplifyBuff(BaseBuff):
    triggers = ['damage', 'heal'] 

    def at_trigger(self, trigger, **kwargs):
        if trigger == 'damage': print('Damage trigger called!')
        if trigger == 'heal': print('Heal trigger called!')
```

### Ticking

A buff with ticking isn't much different than one which triggers. You're still executing arbitrary code off
the buff class. The main thing is you need to have a `tickrate` higher than 1.
```
# this buff will tick 6 times between application and cleanup.
duration = 30
tickrate = 5
def at_tick(self, initial, **kwargs):
    self.owner.take_damage(10)
```
It's important to note the buff always ticks once when applied. For this first tick only, `initial` will be True 
in the `at_tick` hook method.

### Extras

Buffs have a grab-bag of extra functionality to make your life easier!

You can restrict whether or not the buff will check or trigger through defining the `conditional` hook. As long
as it returns a "truthy" value, the buff apply itself. This is useful for making buffs dependent on game state - for
example, if you want a buff that makes the player take more damage when they are on fire.

```python
def conditional(self, *args, **kwargs):
    if self.owner.buffs.get_by_type(FireBuff): return True
    return False
```

There are a number of helper methods. If you have a buff instance - for example, because you got the buff with
`handler.get(key)` - you can `pause`, `unpause`, `remove`, `dispel`, etc.

Finally, if your handler has `autopause` enabled, any buffs with truthy `playtime` value will automatically pause
and unpause when the object the handler is attached to is puppetted or unpuppetted. This even works with ticking buffs,
although if you have less than 1 second of tick duration remaining, it will round up to 1s.

### How Does It Work?

Buffs are stored in two parts alongside each other in the cache: a reference to the buff class, and as mutable data.
You can technically store any information you like in the cache; by default, it's all the basic timing and event
information necessary for the system to run. When the buff is instanced, this cache is fed to the constructor

When you use the handler to get a buff, you get an instanced version of that buff created from these two parts, or
a dictionary of these buffs in the format of {uid: instance}. Buffs are only instanced as long as is necessary to
run methods on them.

#### Context

You may have noticed that almost every important handler method also passes a `context` dictionary.

Context is an important concept for this handler. Every method which modifies, triggers, or checks a buff passes this 
dictionary (default: empty) to the buff hook methods as keyword arguments (**kwargs). This allows you to make those 
methods "event-aware" by storing relevant data in the dictionary you feed to the method.

For example, let's say you want a "thorns" buff which damages enemies that attack you. Let's take our `take_damage` method
and add a context to the mix.

```
def take_damage(attacker, damage):
    context = {'attacker': attacker, 'damage': damage}
    _damage = self.buffs.check(damage, 'taken_damage', context=context)
    self.db.health -= _damage
```
Now we use the values that context passes to the buff kwargs to customize our logic.
```
triggers = ['taken_damage']
# This is the hook method on our thorns buff
def at_trigger(self, trigger, attacker=None, damage=0, **kwargs):
    if not attacker: return
    attacker.db.health -= damage * 0.2
```
Apply the buff, take damage, and watch the thorns buff do its work!

"""    

import time
from evennia.server import signals
from evennia.utils import utils, search
from evennia.typeclasses.attributes import AttributeProperty

class BaseBuff():    
    key = 'template'        # The buff's unique key. Will be used as the buff's key in the handler
    name = 'Template'       # The buff's name. Used for user messaging
    flavor = 'Template'     # The buff's flavor text. Used for user messaging
    visible = True          # If the buff is considered "visible" to the "view" method

    triggers = []       # The effect's trigger strings, used for functions.

    handler = None
    start = 0
    duration = -1       # Default buff duration; -1 or lower for permanent buff, 0 for an "instant" buff (removed immediately after it is added)

    playtime = False    # Does this buff pause automatically when the puppet its own is unpuppetted? No effect on objects that won't be puppetted.

    refresh = True      # Does the buff refresh its timer on application?
    unique = True       # Does the buff overwrite existing buffs with the same key on the same target?
    maxstacks = 1       # The maximum number of stacks the buff can have. If >1, this buff will stack.
    stacks = 1          # If >1, used as the default when applying this buff
    tickrate = 0        # How frequent does this buff tick, in seconds (cannot be lower than 1)
    
    mods = []   # List of mod objects. See Mod class below for more detail
    
    @property
    def ticknum(self):
        '''Returns how many ticks this buff has gone through as an integer.'''
        x = (time.time() - self.start) / self.tickrate
        return int(x)

    @property
    def owner(self):
        if not self.handler: return None
        return self.handler.owner

    @property
    def ticking(self)-> bool:
        '''Returns if this buff ticks or not (tickrate => 1)'''
        return self.tickrate >= 1

    @property
    def stacking(self) -> bool:
        '''Returns if this buff stacks or not (maxstacks > 1)'''
        return self.maxstacks > 1

    def __init__(self, handler, uid, cache={}) -> None:
        self.handler: BuffHandler = handler
        self.uid = uid
        if not cache: cache = dict(self.handler.db.get(uid))
        self.start = cache.get('start')
        self.duration = cache.get('duration')
        self.prevtick = cache.get('prevtick')
        self.paused = cache.get('paused')
        self.stacks = cache.get('stacks')
        self.source = cache.get('source')

    def conditional(self, *args, **kwargs):
        '''Hook function for conditional stat mods. This must return True in 
        order for a mod to be applied, or a trigger to fire.'''
        return True
    
    #region helper methods
    def remove(self, loud=True, expire=False, context={}):
        '''Helper method which removes this buff from its handler.'''
        self.handler.remove(self.uid, loud=loud, expire=expire, context=context)

    def dispel(self, loud=True, delay=0, context={}):
        '''Helper method which dispels this buff (removes and calls at_dispel).'''
        self.handler.remove(self.uid, loud=loud, dispel=True, delay=delay, context=context)

    def pause(self, context={}):
        '''Helper method which pauses this buff on its handler.'''
        self.handler.pause(self.uid, context)

    def unpause(self, context={}):
        '''Helper method which unpauses this buff on its handler.'''
        self.handler.unpause(self.uid, context)

    def reset(self):
        '''Resets the buff start time as though it were just applied; functionally identical to a refresh'''
        self.handler.db[self.uid]['start'] = time.time()
    #endregion
    
    #region hook methods
    def at_apply(self, *args, **kwargs):
        '''Hook function to run when this buff is applied to an object.'''
        pass
    
    def at_remove(self, *args, **kwargs):
        '''Hook function to run when this buff is removed from an object.'''
        pass

    def at_dispel(self, *args, **kwargs):
        '''Hook function to run when this buff is dispelled from an object (removed by someone other than the buff holder).'''
        pass

    def at_expire(self, *args, **kwargs):
        '''Hook function to run when this buff expires from an object.'''
        pass

    def at_pre_check(self, *args, **kwargs):
        '''Hook function to run before this buff's modifiers are checked.'''
        pass
    
    def at_post_check(self, *args, **kwargs):
        '''Hook function to run after this buff's mods are checked.'''
        pass

    def at_trigger(self, trigger:str, *args, **kwargs):
        '''Hook for the code you want to run whenever the effect is triggered.
        Passes the trigger string to the function, so you can have multiple
        triggers on one buff.'''
        pass

    def at_tick(self, initial: bool, *args, **kwargs):
        '''Hook for actions that occur per-tick, a designer-set sub-duration.
        `initial` tells you if it's the first tick that happens (when a buff is applied).'''
        pass

    def at_pause(self, *args, **kwargs):
        '''Hook for when this buff is paused'''
        pass

    def at_unpause(self, *args, **kwargs):
        '''Hook for when this buff is unpaused.'''
        pass
    #endregion

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
    
    ownerref = None
    dbkey = "buffs"
    autopause = False
    _owner = None
    
    def __init__(self, owner, dbkey=dbkey, autopause=autopause):
        self.ownerref = owner.dbref
        self.dbkey = dbkey
        self.autopause = autopause
        if autopause:
            signals.SIGNAL_OBJECT_POST_UNPUPPET.connect(self.pause_playtime)
            signals.SIGNAL_OBJECT_POST_PUPPET.connect(self.unpause_playtime)

    #region properties
    @property
    def owner(self):
        if self.ownerref: _owner = search.search_object(self.ownerref)
        if _owner: return _owner[0]
        else: return None

    @property
    def db(self):
        '''The object attribute we use for the buff database. Auto-creates if not present.'''
        if not self.owner: return {}
        if not self.owner.attributes.has(self.dbkey): self.owner.attributes.add(self.dbkey, {})
        return self.owner.attributes.get(self.dbkey)

    @property
    def traits(self):
        '''All buffs on this handler that modify a stat.'''
        _t = {k:buff for k,buff in self.get_all().items() if buff.mods}
        return _t

    @property
    def effects(self):
        '''All buffs on this handler that trigger off an event.'''
        _e = {k:buff for k,buff in self.get_all().items() if buff.triggers}
        return _e

    @property
    def playtime(self):
        '''All buffs on this handler that only count down during active playtime.'''
        _pt = {k:buff for k,buff in self.get_all().items() if buff.playtime}
        return _pt

    @property
    def paused(self):
        '''All buffs on this handler that are paused.'''
        _p = {k:buff for k,buff in self.get_all().items() if buff.paused}
        return _p

    @property
    def expired(self):
        '''All buffs on this handler that have expired.'''
        _e = { k:buff
            for k,buff in self.get_all().items()
            if not buff.paused
            if buff.duration > -1 
            if buff.duration < time.time() - buff.start }
        return _e

    @property
    def visible(self):
        '''All buffs on this handler that are visible.'''
        _v = { k:buff
            for k,buff in self.get_all().items()
            if buff.visible }
        return _v

    @property
    def all(self):
        '''Returns dictionary of instanced buffs equivalent to ALL buffs on this handler, 
        regardless of state, type, or anything else. You will only need this to extend 
        handler functionality. It is otherwise unused.'''
        _a = self.get_all()
        return _a
    #endregion
    
    #region methods
    def add(self, buff: BaseBuff, key:str=None,
        stacks=0, duration=None, source=None,
        to_cache:dict={},context:dict={}, *args, **kwargs
        ):
        
        '''Add a buff to this object, respecting all stacking/refresh/reapplication rules. Takes
        a number of optional parameters to allow for customization.
        
        Args:
            buff:       The buff class type you wish to add
            source:     (optional) The source of this buff.
            stacks:     (optional) The number of stacks you want to add, if the buff is stacking
            duration:   (optional) The amount of time, in seconds, you want the buff to last. 
            to_cache:   (optional) A dictionary to store in the buff's cache; does not overwrite default cache keys
            context:    (optional) An existing context you want to add buff details to
        '''
        if not isinstance(buff, type): raise ValueError

        _context = context
        source = self.owner
        b = to_cache
        if stacks <1: stacks = min(1, buff.stacks)

        # Create the buff dict that holds a reference and all runtime information.
        b.update({ 
            'ref': buff,
            'start': time.time(),
            'duration': buff.duration, 
            'prevtick': time.time(),
            'paused': False, 
            'stacks': stacks,
            'source': source  
            })

        # Generate the pID (procedural ID) from the object's dbref (uID) and buff key. 
        # This is the actual key the buff uses on the dictionary
        uid = key
        if not uid:
            if source: mix = str(source.dbref).replace("#","")
            uid = buff.key if buff.unique is True else buff.key + mix
        
        # Rules for applying over an existing buff
        if uid in self.db.keys():
            existing = dict(self.db[uid])
            # Stacking
            if buff.maxstacks>1: b['stacks'] = min( existing['stacks'] + stacks, buff.maxstacks )
            elif buff.maxstacks<1: b['stacks'] = existing['stacks'] + stacks
            # Carrying over old arbitrary cache values
            cur_cache = {k:v for k,v in existing.items() if k not in b.keys()}
            b.update(cur_cache)
        # Setting duration and initial tick, if relevant
        if duration: b['duration'] = duration

        # Apply the buff!
        self.db[uid] = b

        # Create the buff instance and run the on-application hook method
        instance: BaseBuff = self.get(uid)
        instance.at_apply(**_context)
        if instance.ticking: tick_buff(self, uid, _context)
        
        # Clean up the buff at the end of its duration through a delayed cleanup call
        if b['duration'] > -1: utils.delay( b['duration'], self.cleanup, persistent=True )

    def remove(self, buffkey, 
        stacks=0, loud=True, dispel=False, expire=False, 
        context={}, *args, **kwargs
        ):
        '''Remove a buff or effect with matching key from this object. Normally calls at_remove,
        calls at_expire if the buff expired naturally, and optionally calls at_dispel. Can also
        remove stacks instead of the entire buff (still calls at_remove)
        
        Args:
            key:    The buff key
            loud:   Calls at_remove when True. Default remove hook.
            dispel: Calls at_dispel when True
            expire: Calls at_expire when True. Used when cleaned up.
'''

        if buffkey not in self.db: return None
        
        buff: BaseBuff = self.db[buffkey]['ref']
        instance : BaseBuff = buff(self, buffkey)
        
        if loud:
            if dispel: instance.at_dispel(**context)
            elif expire: instance.at_expire(**context)
            instance.at_remove(**context)

        del instance
        if not stacks: del self.db[buffkey]
        elif stacks: self.db[buffkey]['stacks'] -= stacks
    
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
                if dispel: instance.at_dispel(**context)
                elif expire: instance.at_expire(**context)
                instance.at_remove(**context)
            del instance
            del self.db[k]

        return _context
        
    def get(self, buffkey: str):
        '''If the specified key is on this handler, return the instanced buff. Otherwise return None.
        You should delete this when you're done with it, so that garbage collection doesn't have to.'''
        buff = self.db.get(buffkey)
        if buff: return buff["ref"](self, buffkey)
        else: return None

    def get_all(self):
        '''Returns a dictionary of instanced buffs (all of them) on this handler in the format {uid, instance}'''
        _cache = dict(self.db)
        return {k:buff['ref'](self, k, cache=buff) for k,buff in _cache.items()}

    def get_by_type(self, buff:BaseBuff):
        '''Returns a dictionary of instanced buffs of the specified type in the format {uid: instance}.'''
        _cache = self.get_all()
        return {k:_buff for k,_buff in _cache.items() if isinstance(_buff, buff)}

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

    def check(self, value: float, stat: str, loud=True, context={}):    
        '''Finds all buffs and perks related to a stat and applies their effects.
        
        Args:
            value: The value you intend to modify
            stat: The string that designates which stat buffs you want
            
        Returns the value modified by relevant buffs.'''
        # Buff cleanup to make sure all buffs are valid before processing
        self.cleanup()

        # Find all buffs and traits related to the specified stat.
        applied = self.get_by_stat(stat, context)
        if not applied: return value
        for buff in applied.values(): buff.at_pre_check(**context)

        # The final result
        final = self._calculate_mods(value, stat, applied)

        # Run the "after check" functions on all relevant buffs
        for buff in applied.values():
            buff: BaseBuff
            if loud: buff.at_post_check(**context)
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
                buff.at_trigger(trigger, **context)
    
    def pause(self, key: str, context={}):
        """Pauses the buff. This excludes it from being checked for mods, triggered, or cleaned up. 
        Used to make buffs 'playtime' instead of 'realtime'."""
        if key in self.db.keys():
            # Mark the buff as paused
            buff = dict(self.db[key])
            if buff['paused']: return
            buff['paused'] = True

            # Math assignments
            t = time.time()         # Current Time
            s = buff['start']       # Start
            d = buff['duration']    # Duration
            pt = buff['prevtick']   # Previous tick timestamp
            tr = buff['ref'].tickrate   # Buff's tick rate
            
            # New duration and tick left
            e = s + d               # End
            nd = e - t              # New duration

            if buff['ref'].ticking == True: pass

            # Apply the new duration
            if nd > 0: 
                buff['duration'] = nd
                if buff['ref'].ticking: buff['tickleft'] = max(1, tr - (t - pt))
                self.db[key] = buff
                instance: BaseBuff = buff['ref'](self, key)
                instance.at_pause(**context) 
            else: self.remove(key)
        return

    def unpause(self, key: str, context={}):
        '''Unpauses a buff. This makes it visible to the various buff systems again.'''
        if key in self.db.keys():
            # Mark the buff as unpaused
            buff = dict(self.db[key])
            if not buff['paused']: return
            buff['paused'] = False

            # Math assignments
            tr = buff['ref'].tickrate
            if buff['ref'].ticking: tl = buff['tickleft']
            t = time.time()         # Current Time

            # Start our new timer, adjust prevtik
            buff['start'] = t
            if buff['ref'].ticking: buff['prevtick'] = t - (tr - tl)
            self.db[key] = buff
            instance: BaseBuff = buff['ref'](self, key)
            instance.at_unpause(**context)  
            utils.delay( buff['duration'], cleanup_buffs, self, persistent=True )
            utils.delay( tr, tick_buff, handler=self, uid=key, initial=False, persistent=True)
        return

    def pause_playtime(self, sender=owner, **kwargs):
        '''Pauses all playtime buffs when attached object is puppeted.'''
        if sender != self.owner: return
        buffs = self.playtime
        for buff in buffs.values(): buff.pause()

    def unpause_playtime(self, sender=owner, **kwargs):
        '''Unpauses all playtime buffs when attached object is unpuppeted.'''
        if sender != self.owner: return
        buffs = self.playtime
        for buff in buffs.values(): buff.unpause()
        pass

    def set_duration(self, key, value):
        '''Modifies the duration of a buff.'''
        if key in self.db.keys():
           self.db[key]['duration'] = value

    def view(self) -> list:
        '''Returns a buff flavor text as a dictionary of tuples in the format {key: (name, flavor)}. Common use for this is a buff readout of some kind.'''
        self.cleanup()
        _flavor = {
            k:(buff.name, buff.flavor)
            for k, buff in self.visible
        }
        
        return _flavor

    def cleanup(self):
        '''Removes expired buffs, ensures pause state is respected.'''
        self.validate_state()
        cleanup_buffs(self)

    def validate_state(self):
        '''Validates the state of paused/unpaused playtime buffs.'''
        if not self.autopause: return
        if self.owner.has_account: self.unpause_playtime()
        elif not self.owner.has_account: self.pause_playtime() 

    #region private methods
    def _calculate_mods(self, value, stat:str, buffs:dict):
        '''Calculates a return value from a base value, a stat string, and a dictionary of instanced buffs with associated mods.'''
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
        
        final = (value + add) * max(0, 1.0 + mult)
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

def tick_buff(handler: BuffHandler, uid: str, context={}, initial=True):
    '''Ticks a buff. If a buff's tickrate is 1 or larger, this is called when the buff is applied, and then once per tick cycle.'''
    # Cache a reference and find the buff on the object
    if uid not in handler.db.keys(): return

    # Instantiate the buff and tickrate
    buff: BaseBuff = handler.get(uid)
    tr = buff.tickrate

    # This stops the old ticking process if you refresh/stack the buff
    if tr > time.time() - buff.prevtick and initial != True: return

    # Always tick this buff on initial
    if initial: buff.at_tick(initial, **context)

    # Tick this buff one last time, then remove
    if buff.duration <= time.time() - buff.start:
        if tr < time.time() - buff.prevtick: buff.at_tick(initial, **context)
        buff.remove(expire=True)
        return

    # Tick this buff on-time
    if tr <= time.time() - buff.prevtick: buff.at_tick(initial, **context)
    
    handler.db[uid]['prevtick'] = time.time()

    # Recur this function at the tickrate interval, if it didn't stop/fail
    utils.delay(tr, tick_buff, handler=handler, uid=uid, context=context, initial=False, persistent=True)