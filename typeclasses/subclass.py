from evennia import CmdSet, utils
from typeclasses.buff import Perk, Mod

class JobHandler(object):
    obj = None

    def __init__(self, obj) -> None:
        self.obj = obj
        if not self.obj.has('jobs'): self.obj.db.jobs = {}
    
    @property 
    def db(self):
        return self.obj.db.jobs


def add_xp(self, xp: int):
        '''Adds XP to this object, respecting all capacity rules.'''
        _xp = self.buffs.check(xp, 'xp')
        self.db.xp = min(self.db.xp + _xp, self.xpCap)

def learn_xp(self):
    '''Learns XP, permanent adding it to your current subclass' pool. If your subclass is capped or you have no xp, nothing happens.
    
    Returns the amount of XP you learned.'''
    subclasses : dict = self.db.subclasses
    subclass : str = self.db.subclass

    if self.db.xp <= 0: return
    if subclass not in subclasses.keys(): return

    _learn = min(self.db.xp, self.xpGain)

    subclasses[subclass]['xp'] += _learn
    self.db.xp -= _learn

    check_for_level(self, subclass)

    return _learn

class Job():
    '''A bundle of job information. Used to set traits and grant access to the class' command sets.'''
    id = ''

    commands: CmdSet = None

    levelCap = 0        # Level cap for this subclass
    xpToNext = 1000     # How much XP it takes to level up
    levelScalar = 1.0   # How much to modify xpToNext based on subclass level. xpToNext *= (level * levelScalar)

    traits = {}
    abilities = {}


    def add_traits(self, target, level):
        '''Function which adds traits whenever you level. Should not be overloaded.'''
        if level in self.traits: target.perks.add(self.traits[level])
            
    def on_level(self, target):
        '''Hook function which fires off after you level'''

def add_subclass(target, subclass: Subclass):
    '''Adds the specified subclass to the target, if it doesn't have it already.'''
    subclasses = target.db.subclasses
    _ref : Subclass = subclass()
    if subclass.id in subclasses.keys(): return
    
    sc = {'ref': subclass, 'level': 1, 'xp': 0}
    _ref.add_traits(target, 1)

    subclasses[subclass.id] = sc

def swap_subclass(target, subclass: Subclass):
    '''Swaps to the specified subclass'''

def check_for_level(target, subclass):
    '''Checks to see if it's time to level up yet. If it is, level up!'''
    
    subclasses = target.db.subclasses
    sc_id = None

    if utils.inherits_from(subclass, str): sc_id = subclass
    if utils.inherits_from(subclass, Subclass): sc_id = subclass.id
    
    if sc_id not in subclasses.keys(): return

    _sc : dict = subclasses[sc_id]
    _ref: Subclass = _sc.get('ref')()
    toNext = _ref.xpToNext * (_sc.get('level') * _ref.levelScalar)

    if _sc.get('xp') >= toNext:
        _sc['xp'] -= toNext
        _sc['level'] += 1
        _ref.add_traits(target, _sc['level'])
        _ref.on_level(target, _sc['level'])