import time
import copy
from evennia.utils import utils

class Context():
    '''A container for "event context" information. Used to pass event information between functions and objects, mostly for buffs and combat.'''
    origin = None
    target = None

    # Combat context information
    weapon = None
    damage = None

    # Buff context information
    _buff = None
    buffID = None
    buffStart = None
    buffStacks = None
    buffDuration = None
    buffApplier = None
    buffPrevTick = None
    buffHandler = None

    @property
    def weaponOwner(self):
        _owner = None
        if self.weapon: _owner = self.weapon.location
        return _owner

    @property
    def buff(self):
        return self._buff
    @buff.setter
    def buff(self, buff):
        self._buff = buff
        _keys = buff.keys()
        self.buffID = buff['uid'] if 'uid' in buff.keys() and buff['uid'] is not None else buff['ref'].id
        if 'start' in _keys: self.buffStart = self.buff['start']
        if 'stacks' in _keys: self.buffStacks = self.buff['stacks']
        if 'duration' in _keys: self.buffDuration = self.buff['duration']
        if 'prevtick' in _keys: self.buffPrevTick = self.buff['prevtick']

        # self.origin.msg('Debug Last Tick: ' + str(self.buffPrevTick) )
        # self.origin.msg('Debug ID: ' + str(self.buffID) )

    def __init__(self, origin, target, weapon=None, damage=None, buff=None, handler=None) -> None:
        
        self.origin = origin
        self.target = target
        if weapon:
            self.weapon = weapon
            self.damage = damage
        
        if buff:
            self.buff = buff
            self.buffHandler = handler