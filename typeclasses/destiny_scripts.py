import random
import time
from typeclasses.scripts import Script

class ShieldRegen(Script): 
    """
    A timer which periodically regenerates your shields.

    This script is actively placed on all character classes at init.
    It pauses when the character takes damage or their shield is at max
    It resumes after shield['delay'] time has passed
    """
    def at_script_creation(self):
        self.key = "shield_regen"
        self.desc = "Regenerates shields if target doesn't take damage for a short period of time"
        self.interval = 1  # Shield regen ticks every second
        self.persistent = True  # Will survive reload
        self.start_delay = True

        self.db.msged = False

        self.db._name = ""

        # If this script is on an object with no shields, it will be removed on start
        if self.obj.db.shield['max'] is None:
            self.obj.scripts.delete(self)

        self.db._name = self.obj.key
        if self.obj.db.named is False:
            self.db._name = "The " + self.db._name

    def at_start(self):
        self.db.msged = False
        self.interval = self.obj.db.shield['delay']

    def at_repeat(self):
        "called every self.interval seconds."            
        now = time.time()
        self.interval = 1

        # Caching basically every shield variable for easy comparison
        lh = self.obj.db.shield['lasthit']
        _curr = self.obj.db.shield['current']
        _max = self.obj.db.shield['max']
        _rg = self.obj.db.shield['regen']
        _delay = self.obj.db.shield['delay']

        # If you haven't been hit recently or your shield is equal or higher than your max, stop regenerating
        if _curr >= _max:
            self.pause()
            return

        # If delay amount of time has passed since you were last hit, and your shield is lower than the max, regenerate each tick
        if now - lh > _delay and _curr < _max:
            self.obj.db.shield['current'] += _rg
            self.obj.db.shield['current'] = min(self.obj.db.shield['current'], _max)

            if self.db.msged is False:
                self.obj.msg("Your shield glimmers and grows more opaque")
                self.obj.location.msg_contents("%s's shield glimmers and grows more opaque." % self.db._name, exclude=self.obj)
                self.db.msged = True
            else:
                return
            
