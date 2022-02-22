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
    '''Learns XP, permanent adding it to your current job' pool. If your job is capped or you have no xp, nothing happens.
    
    Returns the amount of XP you learned.'''
    subclasses : dict = self.db.subclasses
    job : str = self.db.job

    if self.db.xp <= 0: return
    if job not in subclasses.keys(): return

    _learn = min(self.db.xp, self.xpGain)

    subclasses[job]['xp'] += _learn
    self.db.xp -= _learn

    check_for_level(self, job)

    return _learn

class Job():
    '''A bundle of job information. Used to set traits and grant access to the class' command sets.'''
    id = ''

    commands: CmdSet = None

    levelCap = 0        # Level cap for this job
    xpToNext = 1000     # How much XP it takes to level up
    levelScalar = 1.0   # How much to modify xpToNext based on job level. xpToNext *= (level * levelScalar)

    traits = {}
    abilities = {}

    def add_traits(self, target, level):
        '''Function which adds traits whenever you level. Should not be overloaded.'''
        if level in self.traits: target.perks.add(self.traits[level])
            
    def on_level(self, target):
        '''Hook function which fires off after you level'''

def add_subclass(target, job):
    '''Adds the specified job to the target, if it doesn't have it already.'''
    subclasses = target.db.subclasses
    _ref = job()
    if job.id in subclasses.keys(): return
    
    sc = {'ref': job, 'level': 1, 'xp': 0}
    _ref.add_traits(target, 1)

    subclasses[job.id] = sc

def swap_subclass(target, job):
    '''Swaps to the specified job'''

def check_for_level(target, job):
    '''Checks to see if it's time to level up yet. If it is, level up!'''
    
    subclasses = target.db.subclasses
    sc_id = None

    if utils.inherits_from(job, str): sc_id = job
    if utils.inherits_from(job, Job): sc_id = job.id
    
    if sc_id not in subclasses.keys(): return

    _sc : dict = subclasses[sc_id]
    _ref: job = _sc.get('ref')()
    toNext = _ref.xpToNext * (_sc.get('level') * _ref.levelScalar)

    if _sc.get('xp') >= toNext:
        _sc['xp'] -= toNext
        _sc['level'] += 1
        _ref.add_traits(target, _sc['level'])
        _ref.on_level(target, _sc['level'])