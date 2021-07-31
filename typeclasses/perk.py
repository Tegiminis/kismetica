from buffhandler import add_buff
from perkinit import PerkList as perks

class BasePerk():
    
    slot = None           # The perk's slot. If not None, will use this for the perk's dict key
    id = ''             # Perk's unique ID. If slot is None, will use this for the perk's dict key
    trigger = ''        # The perk's trigger string, used for functions
    release = ''        # The perk's release string, used for functions

    def on_trigger(context):
        '''Hook for the code you want to run whenever the perk is triggered. Required.'''
        pass

    def on_release(context):
        '''Hook for the code you want to run whenever the perk is released (reverse of trigger). Optional.'''
        pass

def trigger_perk(trigger: str, context):
    activate = [k for k,v in context.db.perkhandler.items() if v.trigger == trigger]
    for x in activate: context.db.perkhandler[x].on_trigger(context)

def add_perk(ref: str, context):
    '''Adds the referenced perk to the context's perkhandler. Must match variable name in perkinit.py exactly.'''
    p : BasePerk = vars(perks).get(ref)
    id = p.id
    slot = p.slot

    if slot: context.db.perkhandler[slot] = p
    else: context.db.perkhandler[id] = p
