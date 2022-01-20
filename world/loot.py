import random
import evennia
from evennia.utils.utils import inherits_from
from typeclasses.weapon import Weapon
from typeclasses.context import Context
import typeclasses.content.perklist as pl

class NPCStub():
    '''This is just my little organizational tool for figuring out the system of looting
    
    Process:
        1.  Kill enemy
        2.  Use loot command on corpse
        3.  Each entry in "loot rolls" table is rolled on
        4.  If roll is successful, returns the loot table to continue rolling on for a (guaranteed) reward
        5.  If it is a reward that can have perks, it randomly generates a number of perks, based on the item rarity
    '''

class TestWeapon(Weapon):
    
    def roll_perks(self, perks, slot):
        _toApply = roll_on_table(perks)
        self.perks.add(_toApply, slot)

    def at_object_creation(self):
        "Called when object is first created"
        super().at_object_creation()
        
        slot1 = [(pl.ExploitPerk, 5), 
            (pl.RampagePerk, 5),
            (pl.LeechRoundPerk, 5)]

        self.roll_perks(slot1, "slot1")

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

def roll(chance: float):
    '''Returns true if the roll is under chance, otherwise returns False. Chance should be a number between 0.0 and 1.0.'''
    roll = random.random()
    if (roll <= chance): return True
    else: return False

def roll_on_table(table: list, context: Context = None):
    '''Takes a list of tuples with the format (value, chance) and rolls to find which one to return. Guaranteed to return a value.'''
    _total = 0
    for x in table: _total += x[1]
    
    if context: context.origin.msg("Debug: Loot Weight: " + str(x[1]))
            
    for x in table:
        if ( roll(x[1] / _total) ): return x[0]
        else: _total -= x[1]

def parse_result(obj, context: Context):
    '''Parses the result of a loot drop. This means creating objects, adding currency, and so on.'''
    if inherits_from(obj, Weapon):
        evennia.create_object(obj, key="test weapon", location=context.origin.location)