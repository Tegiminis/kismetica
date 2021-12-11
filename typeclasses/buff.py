from typeclasses.objects import DefaultObject as Object
from typeclasses.context import BuffContext

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

    def on_apply(self, context: BuffContext):
        '''Hook function to run when this buff is applied to an object.'''
        pass 
    
    def on_remove(self, context: BuffContext):
        '''Hook function to run when this buff is removed from an object.'''
        pass

    def on_dispel(self, context: BuffContext):
        '''Hook function to run when this buff is dispelled from an object (removed by someone other than the buff holder).'''
        pass

    def on_expire(self, context: BuffContext):
        '''Hook function to run when this buff expires from an object.'''
        pass

    def after_check(self, context: BuffContext):
        '''Hook function to run after this buff's mods are checked.'''
        pass

    def on_trigger(self, context: BuffContext) -> BuffContext:
        '''Hook for the code you want to run whenever the effect is triggered. Required.'''
        pass

    def on_release(self, context: BuffContext) -> BuffContext:
        '''Hook for the code you want to run whenever the effect is released (reverse of trigger). Optional.'''
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
    
    duration = 1                # Buff duration in seconds. Will use this if the add_buff keyword is not overloaded. -1 for a "permanent" buff

    refresh = True              # Does the buff refresh its timer on application?
    stacking = False            # Does the buff stack with itself?
    unique = False              # Does the buff only apply if there is no buff like it on the target?
    maxstacks = 1               # The maximum number of stacks the buff can have.

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