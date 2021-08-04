from typeclasses.objects import DefaultObject as Object

class BasePerk(Object):
    '''The base perk class used in all perk definition'''
    slot = None         # The perk's slot. If not None, will use this for the perk's dict key
    id = ''             # Perk's unique ID. If slot is None, will use this for the perk's dict key
    trigger = ''        # The perk's trigger string, used for functions
    release = ''        # The perk's release string, used for functions
    
    def on_trigger(self, context):
        '''Hook for the code you want to run whenever the perk is triggered. Required.'''
        pass

    def on_release(self, context):
        '''Hook for the code you want to run whenever the perk is released (reverse of trigger). Optional.'''
        pass


