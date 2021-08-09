from typeclasses.context import BuffContext
from typeclasses.objects import DefaultObject as Object
from typeclasses.buff import BaseBuff, Buff

class Perk(BaseBuff):
    '''A permanent effect which fires off when its trigger condition is met.
    
    Vars:
        slot:       If defined, uses this for the perk's dictionary key. Otherwise, uses the perk id.
        trigger:    Trigger string, used to activate it through the perk handler.
        release:    Release string, currently unused.

    Funcs:
        on_trigger: Hook for code to run when the perk is triggered. Required.
        on_release: Hook for code to run when the perk is released.
    '''

    slot = None         # The perk's slot. If not None, will use this for the perk's dict key

    trigger = ''        # The perk's trigger string, used for functions
    release = ''        # The perk's release string, used for functions
    
    trigger_msg = None

    def on_trigger(self, context: BuffContext) -> BuffContext:
        '''Hook for the code you want to run whenever the perk is triggered. Returns trigger_msg. Required.'''
        return self.trigger_msg

    def on_release(self, context: BuffContext) -> BuffContext:
        '''Hook for the code you want to run whenever the perk is released (reverse of trigger). Optional.'''
        pass

class Effect(Buff):
    '''A perk-like buff that has trigger conditions, allowing it to "fire off" when certain conditions are met.'''
    
    trigger = ''        # The effect's trigger string, used for functions
    release = ''        # The effect's release string, used for functions

    trigger_msg = None

    cooldown = 0

    mods = None

    def on_trigger(self, context: BuffContext) -> BuffContext:
        '''Hook for the code you want to run whenever the effect is triggered. Required.'''
        return self.trigger_msg

    def on_release(self, context: BuffContext) -> BuffContext:
        '''Hook for the code you want to run whenever the effect is released (reverse of trigger). Optional.'''
        pass
