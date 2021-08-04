from typeclasses.objects import DefaultObject as Object

class BaseBuff(Object):
    '''Buffs are temporary stat modifications.
    
    Vars:
        id:         The buff's unique ID. Will be used as the buff's key in the handler
        name:       The buff's name. Used for user messaging
        flavor:     The buff's flavor text. Used for user messaging
        duration:   Buff duration in seconds. Will use this if the add_buff keyword is not overloaded. -1 for a "permanent" buff
        refresh:    Does the buff refresh its timer on application?
        stacking:   Does the buff stack with itself?
        stat:       The stat the buff affects. Essentially a tag used to find the buff for coding purposes  
        maxstacks:  The maximum number of stacks the buff can have.
        base:       Buff's value
        perstack:   How much additional value is added to the buff per stack
        mod:        The modifier the buff applies. "add" for add/sub or "mult" for mult/div'''
    
    id = 'template'             # The buff's unique ID. Will be used as the buff's key in the handler
    name = 'Template'           # The buff's name. Used for user messaging
    flavor = 'Template'         # The buff's flavor text. Used for user messaging

    duration = 1                # Buff duration in seconds. Will use this if the add_buff keyword is not overloaded.  -1 for a "permanent" buff

    refresh = True              # Does the buff refresh its timer on application?
    stacking = False            # Does the buff stack with itself?
    unique = False              # Does the buff only apply if there is no buff like it on the target?
    maxstacks = 1               # The maximum number of stacks the buff can have.

    mods = []

    def on_apply(self, context):
        '''Hook function to run when this buff is applied to an object.
        
        Args:
            context: The object this buff is attached to.'''
        pass 

    def on_remove(self, context):
        '''Hook function to run when this buff is removed from an object.
        
        Args:
            context: The object this buff is attached to.'''
        pass

class Mod():
    '''The stat modification. One buff can hold multiple mods.'''
    
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