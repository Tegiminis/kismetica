import random
from typeclasses.objects import Object
from typeclasses.handlers import buffhandler as bh

class Weapon(Object):
    """
    A weapon that can be used by our illustrious player.
    """
 
    def at_object_creation(self):
        "Called when object is first created"

        self.db.buffs = {}
        self.db.perks = {}

        self.db.cooldowns = {}

        self.db.named = False

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

        # Range stats. Base stat affects upper damage bracket, cqc affects accuracy when enemy range is below, falloff affects damage when enemy range is above
        self.db.range = 10
        self.db.cqc = 1
        self.db.falloff = 3

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
        _name = self.key if self.db.named is True else "the " + self.name
        return _name

    def at_desc(self, looker, **kwargs):
        looker.msg('Stability: ' + str(self.stability))

    #region properties
    @property
    def ammo(self):
        self.db.ammo = min(self.db.ammo, self.maxAmmo)
        return self.db.ammo
    
    @property
    def damage(self):
        _dmg = random.randint(self.damageMin, self.damageMax)
        # self.location.msg('Debug Randomized Damage: ' + str(_dmg))
        _modifiedDmg = bh.check_stat_mods(self, _dmg, 'damage')
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
        _acc = bh.check_stat_mods(self, self.db.accuracy, 'accuracy')
        return _acc

    @property
    def range(self):
        _rng = bh.check_stat_mods(self, self.db.range, 'range')
        return _rng

    @property
    def stability(self):
        _stab = bh.check_stat_mods(self, self.db.stability, 'stability')
        return _stab

    @property
    def maxAmmo(self):
        _ma = bh.check_stat_mods(self, self.db.maxAmmo, 'maxammo')
        return _ma

    @property
    def equip(self):
        _eq = bh.check_stat_mods(self, self.db.equip, 'equip')
        return _eq

    @property
    def reload(self):
        _rl = bh.check_stat_mods(self, self.db.reload, 'reload')
        return _rl

    @property
    def rpm(self):
        _rpm = bh.check_stat_mods(self, self.db.rpm, 'rpm')
        return _rpm

    @property
    def cqc(self):
        _cqc = bh.check_stat_mods(self, self.db.cqc, 'cqc')
        return _cqc

    @property
    def falloff(self):
        _fo = bh.check_stat_mods(self, self.db.falloff, 'falloff')
        _fo += int(self.range / 90)
        return _fo

    @property
    def critChance(self):
        _prec = bh.check_stat_mods(self, self.db.critChance, 'critchance')
        return _prec

    @property
    def critMult(self):
        _hs = bh.check_stat_mods(self, self.db.critMult, 'critmult')
        return _hs

    @property
    def shots(self):
        _shots = bh.check_stat_mods(self, self.db.shots, 'shots')
        return _shots
    
    @property
    def traits(self):
        _perks = [x for x in self.db.perks.values() if x['ref']().mods ]
        _buffs = [x for x in self.db.buffs.values() if x['ref']().mods ]
        # self.location.msg('Debug Modifier Perks And Buffs: ' + str(_perks + _buffs))
        return _perks + _buffs

    @property
    def effects(self):
        _perks = [x for x in self.db.perks.values() if x['ref']().trigger ]
        _buffs = [x for x in self.db.buffs.values() if x['ref']().trigger ]
        _perks.extend(_buffs)
        # self.location.msg("Debug Effects: " + str(_perks))
        return _perks
    #endregion