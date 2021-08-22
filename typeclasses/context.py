from evennia.utils import utils
from typeclasses.weapon import Weapon

class Context():
    '''A container for "context" information. Base class is a relation between two objects: actor and acted upon.'''
    actor = None
    actee = None
    
    def __init__(self, actor, actee) -> None:
        self.actor = actor
        self.actee = actee

class DamageContext(Context):
    '''A container for an individual "damage context", which includes a reference to a weapon and the amount of damage done.'''
    damage = 0
    weapon = None

    def __init__(self, actor, actee, weapon, damage) -> None:
        self.actor = actor
        self.actee = actee
        self.weapon = weapon
        self.damage = damage

class BuffContext(Context):
    '''A container for an individual "buff context", which includes the dictionary key of the buff that was created, stacked, or otherwise accessed.'''
    handler = None
    id = None
    ref = None
    duration = None
    stacks = None
    start = None
    owner = None

    def __init__(self, actor, actee, handler, id) -> None:
        self.actor = actor
        self.actee = actee
        self.handler = handler
        self.id = id
        if utils.inherits_from(actee, Weapon): self.owner = actee.location
        if id in handler.keys():
            self.ref = handler[id]['ref']
            self.duration = handler[id]['duration']
            self.stacks = handler[id]['stacks']
            self.start = handler[id]['start']

def generate_context(actee=None, actor=None, damage=None, weapon=None, buff=None, handler=None) -> Context:
    '''Wrapper function for generating contexts. Takes a type and named arguments to create the context.'''

    if not actor: actor = actee

    context = None

    if damage or weapon:
        context = DamageContext(actor, actee, weapon, damage)
    elif buff or handler:
        context = BuffContext(actor, actee, handler, buff)
    else:
        context = Context(actor, actee)

    return context