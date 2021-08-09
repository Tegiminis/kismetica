from random import choice
from typeclasses.objects import Object
from world import rules

class Weapon(Object):
    """
    A weapon that can be used by our illustrious player.
    """
    def at_object_creation(self):
        "Called when object is first created"

        self.db.buffs = {}
        self.db.perks = {}
        self.db.effects = {}
        self.db.traits = {}
        
        self.db.slot = 'kinetic'
        self.db.element = 'neutral'

        self.db.named = False

        # All ammo-related stats
        self.db.ammo = {
            'type':'primary', # Ammo type used when fired (primary is infinite, others are not)
            'current':30,     # How much ammo the weapon has currently loaded
            'max':30,         # How much ammo the weapon has when fully loaded
            "used":5          # How much ammo the weapon uses when it fires
            }

        # All basic damage- and hit-related stats
        self.db.damage = {
            'base':10,          # Base damage. The quite literal number of hit or shield points this weapon deals, absent any modifiers
            'min':10,            # Minimum damage dealt, not counting damage falloff
            'max':10,           # Maximum damage dealt
            'acc':1.5,          # Base accuracy. Your hit roll is multiplied by this. 1.0 means no change to the hit roll.
            'shots':1,          # How many shots you fire at once. Each shot's accuracy is calculated independently.
            'falloff':2         # Distance where damage falloff starts
        }

        # Innate stats related to "speed", aka action cooldowns
        self.db.speed = {
            'equip':3.0,        # In seconds, time it takes to swap to and from this weapon
            'reload':3.0,       # In seconds, time it takes to reload this weapons
            'fire':3.0          # In seconds, time it takes for this weapon to "cool down" and be ready for use again
            }
        
        # Innate stats related to "range", which influences your hit chances. Anything above max or below min will suffer an accuracy penalty
        self.db.range = {
            'min':1,
            'max':3          
            }
        
        # Innate stats related to "crits", aka precision shots, which multiply your damage
        self.db.crit = {
            'chance':2.0,     # Chance that a shot is "precise", aka a critical. See "hit_roll" in destiny_rules for more
            'mult':2.0        # The multiplier for damage when a precision shot happens
            } 

        # Messages for all the things that your gun does
        self.db.msg = {
            'miss': 'You miss!', 
            'attack':'%s shoots at %s.',
            'equip': '',
            'kill': '%s crumples to the floor, dead.',
            'cooldown': 'You can fire again.'
            }

    # Used for formatting the "stat bars"
    def stat_format(self, key):

        _str = ""   # Create return string object

        for x in range(10):
            if x <= round( self.db.stat[key] / 10 ):
                _str += "█"
            else:
                _str += " "

        return _str

    def return_appearance(self, looker):
        """
        Called by the look command.
        """
        # first get the base string from the
        # parent's return_appearance.
        string = super().return_appearance(looker)
        str_impact = self.stat_format('impact')
        str_acc = self.stat_format('accuracy')

        stats = "\nImpact: |b%s|n" % (str_acc) + "               " + "Accuracy: |r%s|n" % (str_impact)
        
        return string + stats

    def named(self):
        _name = self.key
        if self.db.named is False:
                _name = "the " + _name
        return _name