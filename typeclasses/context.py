from evennia.utils import utils

class Context():
    '''An container for "event context" information. Used to pass event information between functions and objects, mostly for buffs and combat.'''
    origin = None
    target = None
    weapon = None
    damage = None
    buff = None
    handler = None

    #region derived properties
    @property
    def id(self):
        _id = None
        if self.buff:
            _buff = self.buff
            _id = _buff['uid'] if 'uid' in _buff.keys() else _buff['ref'].id
        return _id
    
    @property
    def applier(self):
        _applier = None
        if self.buff:
            if 'origin' in self.buff.keys(): _applier = self.buff['origin']
        return _applier

    @property
    def duration(self):
        _dur = None
        if self.buff:
            if 'duration' in self.buff.keys(): _dur = self.buff['duration']
        return _dur

    @property
    def stacks(self):
        _stacks = None
        if self.buff:
            if 'stacks' in self.buff.keys(): _stacks = self.buff['stacks']
        return _stacks

    @property
    def start(self):
        _start = None
        if self.buff:
            if 'start' in self.buff.keys(): _start = self.buff['start']
        return _start

    @property
    def owner(self):
        _owner = None
        if self.weapon: _owner = self.weapon.location
        return _owner
    #endregion

    def __init__(self, origin, target, weapon=None, damage=None, buff=None, handler=None) -> None:
        self.origin = origin
        self.target = target
        if weapon:
            self.weapon = weapon
            self.damage = damage
        
        if buff:
            self.buff = buff
            self.handler = handler