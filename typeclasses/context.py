from evennia.utils import utils

class Context():
    '''A container for "context" information. Base class is a relation between two objects: origin and acted upon.'''
    origin = None
    target = None
    
    def __init__(self, origin, target) -> None:
        self.origin = origin
        self.target = target

class DamageContext(Context):
    '''A container for an individual "damage context", which includes a reference to a weapon and the amount of damage done.'''
    damage = 0
    weapon = None

    def __init__(self, origin, target, weapon, damage) -> None:
        self.origin = origin
        self.target = target
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
    buff = None
    applier = None
    dc = None

    def __init__(self, origin, target, buff, handler, dc: DamageContext = None) -> None:
        self.origin = origin
        self.target = target
        self.handler = handler
        self.dc = dc
        self.owner = origin.location

        _k = buff.keys()
        self.id = buff ['uid'] if 'uid' in _k else buff['ref'].id

        if 'origin' in _k: self.applier = buff['origin']
        if 'duration' in _k: self.duration = buff['duration']
        if 'stacks' in _k: self.stacks = buff['stacks']
        if 'start' in _k: self.start = buff['start']

def generate_context(origin=None, target=None, damage=None, weapon=None, buff=None, handler=None, dc=None) -> Context:
    '''Wrapper function for generating contexts. Takes a type and named arguments to create the context.'''

    if not origin: origin = target
    if not target: target = origin

    context = None

    if damage and weapon:
        context = DamageContext(origin, target, weapon, damage)
    elif buff and handler:
        context = BuffContext(origin, target, buff, handler, dc)
    else:
        context = Context(origin, target)

    return context