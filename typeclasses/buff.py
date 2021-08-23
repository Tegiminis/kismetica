from typeclasses.context import BuffContext
from typeclasses.objects import DefaultObject as Object

class BaseBuff():
    '''Base class for all "buffs" in the game. Buffs are permanent and temporary modifications to stats, and trigger conditions that run arbitrary code.

    There are 4 kinds of buffs:
        Buff:   Stat modification, temporary
        Trait:  Stat modification, permanent
        Effect: Trigger condition, temporary
        Perk:   Trigger condition, permanent
    Strings:
        id:         The buff's unique ID. Will be used as the buff's key in the handler
        name:       The buff's name. Used for user messaging
        flavor:     The buff's flavor text. Used for user messaging
    '''
    
    id = 'template'             # The buff's unique ID. Will be used as the buff's key in the handler
    name = 'Template'           # The buff's name. Used for user messaging
    flavor = 'Template'         # The buff's flavor text. Used for user messaging

    def on_apply(self, context: BuffContext):
        '''Hook function to run when this buff is applied to an object.'''
        pass 
    
    def on_remove(self, context: BuffContext):
        '''Hook function to run when this buff is removed from an object.'''
        pass

class Buff(BaseBuff):
    '''A buff is comprised of one or more temporary stat modifications.

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
    
    duration = 1                # Buff duration in seconds. Will use this if the add_buff keyword is not overloaded.  -1 for a "permanent" buff

    refresh = True              # Does the buff refresh its timer on application?
    stacking = False            # Does the buff stack with itself?
    unique = False              # Does the buff only apply if there is no buff like it on the target?
    maxstacks = 1               # The maximum number of stacks the buff can have.

    mods = []
    
    def after_check(self, context: BuffContext):
        '''Hook function to run after this buff's mods are checked.'''
        pass

    def on_dispel(self, context: BuffContext):
        '''Hook function to run when this buff is dispelled from an object (removed by someone other than the buff holder).'''
        pass

    def on_expire(self, context: BuffContext):
        '''Hook function to run when this buff expires from an object.'''
        pass

class Trait(BaseBuff):
    '''A trait is comprised of one or more temporary stat modifications.

    Strings:
        id:         The trait's unique ID. Will be used as the trait's key in the handler
        name:       The trait's name. Used for user messaging
        flavor:     The trait's flavor text. Used for user messaging
    Vars:
        mods:       The modifiers the trait applies. See Mod class.'''
    
    mods = []

    pass

class Perk(BaseBuff):
    '''A permanent effect which fires off when its trigger condition is met.
    
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

    trigger = ''        # The perk's trigger string, used for functions
    release = ''        # The perk's release string, used for functions
    
    trigger_msg = None

    def on_trigger(self, context: BuffContext) -> BuffContext:
        '''Hook for the code you want to run whenever the perk is triggered. Returns trigger_msg. Required.'''
        pass

    def on_release(self, context: BuffContext) -> BuffContext:
        '''Hook for the code you want to run whenever the perk is released (reverse of trigger). Optional.'''
        pass

class Effect(Buff):
    '''A perk-like buff that has trigger conditions, allowing it to "fire off" when certain conditions are met.
    
    Strings:
        id:         The buff's unique ID. Will be used as the buff's key in the handler
        name:       The buff's name. Used for user messaging
        flavor:     The buff's flavor text. Used for user messaging
    Vars:
        slot:       If defined, uses this for the effect's dictionary key. Otherwise, uses the effect id.
        trigger:    Trigger string, used to activate it through the effect handler.
        release:    Release string, currently unused.
    Funcs:
        on_trigger: Hook for code to run when the effect is triggered. Required.
        on_release: Hook for code to run when the effect is released.'''
    
    trigger = ''        # The effect's trigger string, used for functions
    release = ''        # The effect's release string, used for functions

    trigger_msg = None

    cooldown = 0

    mods = None

    def on_trigger(self, context: BuffContext) -> BuffContext:
        '''Hook for the code you want to run whenever the effect is triggered. Required.'''
        pass

    def on_release(self, context: BuffContext) -> BuffContext:
        '''Hook for the code you want to run whenever the effect is released (reverse of trigger). Optional.'''
        pass

class Mod():
    '''A single stat modification. One buff or trait can hold multiple mods, for the same or different stats.'''
    
    stat = 'damage'             # The stat the buff affects. Essentially a tag used to find the buff for coding purposes  
    base = 0                    # Buff's value
    perstack = 0                # How much additional value is added to the buff per stack
    modifier = 'add'                 # The modifier the buff applies. 'add' or 'mult' 

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