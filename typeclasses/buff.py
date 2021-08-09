from typeclasses.context import BuffContext
from typeclasses.objects import DefaultObject as Object

class BaseBuff():
    '''Base class for all "buffs" in the game. Buffs are permanent and temporary modifications to stats.

    There are 4 kinds of buffs:
        Buff:   Stat modification, temporary
        Trait:  Stat modification, permanent
        Effect: Trigger condition, temporary
        Perk:   Trigger condition, permanent
    
    Vars:
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

    Vars:
        id:         The buff's unique ID. Will be used as the trait's key in the handler
        name:       The buff's name. Used for user messaging
        flavor:     The buff's flavor text. Used for user messaging
        duration:   Buff duration in seconds. Will use this if the add_buff keyword is not overloaded. -1 for a "permanent" buff
        refresh:    Does the buff refresh its timer on application?
        stacking:   Does the buff stack with itself?
        unique:     Will this buff prevent reapplication until its duration is out?
        maxstacks:  The maximum number of stacks the buff can have.
        mods:       The modifiers the buff applies. See Mod class.'''
    
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

class Trait(Buff):
    '''A trait is comprised of one or more permanent stat modifications.
    
    Vars:
        slot:       If defined, uses this for the perk's dictionary key. Otherwise, uses the perk id.
        id:         The trait's unique ID. Will be used as the trait's key in the handler
        name:       The trait's name. Used for user messaging
        flavor:     The trait's flavor text. Used for user messaging
        mods:       The modifiers the trait applies. See Mod class'''

    slot = ''
    
    duration = -1

    pass

class Mod():
    '''A single stat modification. One buff or trait can hold multiple mods, for the same or different stats.'''
    
    stat = 'damage'             # The stat the buff affects. Essentially a tag used to find the buff for coding purposes  
    base = 0                    # Buff's value
    perstack = 0                # How much additional value is added to the buff per stack
    modifier = 'add'                 # The modifier the buff applies. 'add' or 'mult' 

    def __init__(self, stat: str, modifier: str, base, perstack) -> None:
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