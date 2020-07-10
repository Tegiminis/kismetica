from random import choice
from typeclasses.objects import Object
from world import destiny_rules

class Weapon(Object):
    """
    A weapon that can be used by our illustrious player.
    """
    def at_object_creation(self):
        "Called when object is first created"

        self.db.slot = 'kinetic'
        self.db.element = 'neutral'

        # All ammo-related stats
        self.db.ammo = {
            'type':'primary', # Ammo type used when fired (primary is infinite, others are not)
            'current':30,     # How much ammo the weapon has currently loaded
            'max':30,         # How much ammo the weapon has when fully loaded
            "used":5          # How much ammo the weapon uses when it fires
            }
        
        # All player-facing stats, used for doing damage and hit calculations and the like.
        # These stats "modify" a weapon's archetype, or "base", stats
        self.db.stat = {
            'impact':50,      # Damage.
            'accuracy':50,    # Base accuracy; 50 means no change to base accuracy
            'stability':100,  # How much accuracy changes each time you fire; 100 means it doesn't.
            'range':50,       # How "utilized" your weapon's range stats are; 50 means "mostly"
            'handling':50,    # How fast you swap weapons; 50 means no change
            'reload':50,      # How quickly you reload; 50 means no change
            'rpm':50          # The weapon's rate of fire; 50 means no change
            }

        # All basic damage- and hit-related stats
        self.db.damage = {
            'base':10,      # Base damage. The quite literal number of hit or shield points this weapon deals, absent any modifiers
            'accuracy':1.0,   # Base accuracy. Your hit roll is multiplied by this. 1.0 means no change to the hit roll.
            'shots':5,        # How many shots you fire at once. Each shot's accuracy is calculated independently.
            'falloff':8.0     # Distance where damage falloff starts, out to max (where shots no longer hit)
        }

        # Innate stats related to "speed", aka action cooldowns
        self.db.speed = {
            'equip':3.0,      # In seconds, time it takes to swap to and from this weapon
            'reload':3.0,     # In seconds, time it takes to reload this weapons
            'fire':3.0        # In seconds, time it takes for this weapon to "cool down" and be ready for use again
            }
        
        # Innate stats related to "range", which influences your hit chances and damage falloff
        self.db.range = {
            'max':10,         # Distance, measured via room_depth, that the weapon will no longer hit the target
            'min':1.0,        # Distance that the weapon suffers a severe accuracy penalty if the target is too close
            }
        
        # Innate stats related to "crits", aka precision shots, which multiply your damage
        self.db.crit = {
            'chance':2.0,     # Chance that a shot is "precise", aka a critical. See "hit_roll" in destiny_rules for more
            'mult':2.0        # The multiplier for damage when a precision shot happens
            } 

        # List of a weapon's perks
        # [Barrel, Magazine, Sight, Style, Style]
        self.db.perks = {'innate':None, 'barrel':None, 'mag':None, 'sight':None, 'style1':None, 'style2':None}

        # Messages for all the things that your gun does
        self.db.msg = {
            'miss': 'You miss!', 
            'attack': 'You shoot at %s!', 
            'equip': 'It feels cold and menacing in your grip.',
            'cooldown': 'You grip your weapon tighter as you prepare for another attack.'
            }

        # Your weapon's current accuracy. Returns to base accuracy over time.
        self.ndb.acc = 1.0
        
    def at_init(self):
        self.ndb.acc = self.db.damage['accuracy']

    def return_appearance(self, looker):
        """
        Called by the look command.
        """
        # first get the base string from the
        # parent's return_appearance.
        string = super().return_appearance(looker)
        impact = ""
        acc = ""

        stats = "\nImpact: |b%s|n | Accuracy: |r%s|n"
        _str_dict = []

        for key in self.db.stat:
            _str_dict[key] = stat_format(key)
        stats = stats % (_str_dict['impact'], _str_dict['accuracy'])
        
        return string + stats

    def stat_format(key):

        _str = ""

        for x in range(10):
            if x == round(self.db.stat[key]/10):
                _str += "▌"
            else:
                _str += " "
    
        return _str