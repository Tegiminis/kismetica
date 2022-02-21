import random
from typeclasses.objects import Object
from typeclasses.buff import BuffHandler, PerkHandler
from evennia.utils import lazy_property

class Weapon(Object):
    """
    A weapon that can be used by player characters.
    """

    @lazy_property
    def buffs(self) -> BuffHandler:
        return BuffHandler(self)

    @lazy_property
    def perks(self) -> PerkHandler:
        return PerkHandler(self)
    
    def at_object_creation(self):
        "Called when object is first created"

        self.db.buffs = {}
        self.db.perks = {}

        # Ammo stats
        self.db.ammo = 30
        self.db.maxAmmo = 30
        
        # Damage stats
        self.db.damage = 10
        self.db.stability = 10

        # Hit/shot stats
        self.db.shots = 1
        self.db.accuracy = 1.0

        # Speed stats for doing particular actions (forces cooldown)
        self.db.equip = 20
        self.db.reload = 15
        self.db.rpm = 5

        # Range stats. 
        self.db.range = 10      # Increases upper damage bracket
        self.db.cqc = 1         # Decrease accuracy when enemy range is lower
        self.db.falloff = 3     # Decrease damage when enemy range is higher

        # Crit chance and multiplier
        self.db.critChance = 2.0
        self.db.critMult = 2.0

        # Messages for all the things that your gun does
        self.db.msg = {
            'miss': 'You miss!', 
            'attack':'%s shoot at %s.',
            'equip': '',
            'kill': '%s crumples to the floor, dead.',
            'cooldown': 'You can fire again.'
            }

        # Gun's rarity. Common, Uncommon, Rare, Legendary, Unique, Exotic. Dictates number of perks when gun is rolled on.
        self.db.rarity = 1
    
    @property
    def named(self):
        if self.tags.get('named') is None: return "the " + self.key
        else: return self.key

    #region properties
    @property
    def ammo(self):
        self.db.ammo = min(self.db.ammo, self.maxAmmo)
        return self.db.ammo
    
    @property
    def damage(self):
        _dmg = random.randint(self.damageMin, self.damageMax)
        # self.location.msg('Debug Randomized Damage: ' + str(_dmg))
        _modifiedDmg = self.buffs.check(_dmg, 'damage')
        # self.location.msg('Debug Modified Damage: ' + str(_modifiedDmg - _dmg))
        return _modifiedDmg

    @property
    def damageMin(self):
        _min = self.db.damage / 2
        return int( _min + ( _min * (self.stability / 100) ) )

    @property
    def damageMax(self):
        _dmg = self.db.damage
        _max = _dmg / 2
        return int( _dmg + _max + (_max * (self.range / 100)) )

    @property
    def accuracy(self):
        _acc = self.buffs.check(self.db.accuracy, 'accuracy')
        return _acc

    @property
    def range(self):
        _rng = self.buffs.check(self.db.range, 'range')
        return _rng

    @property
    def stability(self):
        _stab = self.buffs.check(self.db.stability, 'stability')
        return _stab

    @property
    def maxAmmo(self):
        _ma = self.buffs.check(self.db.maxAmmo, 'maxammo')
        return _ma

    @property
    def equip(self):
        _eq = self.buffs.check(self.db.equip, 'equip')
        return _eq

    @property
    def reload(self):
        _rl = self.buffs.check(self.db.reload, 'reload')
        return _rl

    @property
    def rpm(self):
        _rpm = self.buffs.check(self.db.rpm, 'rpm')
        return _rpm

    @property
    def cqc(self):
        _cqc = self.buffs.check(self.db.cqc, 'cqc')
        return _cqc

    @property
    def falloff(self):
        '''The range at which you see a 20% damage penalty. This must be higher
        than a defender's range in order to avoid damage penalty. Having a
        high range stat can buff this by one tier.'''
        _fo += int(self.range / 90)
        _fo = self.buffs.check(self.db.falloff, 'falloff')
        return _fo

    @property
    def critChance(self):
        _prec = self.buffs.check(self.db.critChance, 'critchance')
        return _prec

    @property
    def critMult(self):
        _hs = self.buffs.check(self.db.critMult, 'critmult')
        return _hs

    @property
    def shots(self):
        _shots = self.buffs.check(self.db.shots, 'shots')
        return _shots
    
    @property
    def traits(self):
        _buffs = self.buffs.traits
        _perks = self.buffs.perks
        return _perks + _buffs

    @property
    def effects(self):
        _perks = self.perks.effects
        _buffs = self.buffs.effects
        return _perks + _buffs
    #endregion