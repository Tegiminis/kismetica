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
        self.interval = self.obj.db.shield['delay']     # Shield regen ticks every second
        self.persistent = True      # Will survive reload
        self.start_delay = True

        self.tags.add( 'on_hit' )

        self.db.msged = False

        # If this script is on an object with no shields, it will be removed on start
        if self.obj.db.shield['max'] is None:
            self.obj.scripts.delete(self)

    def at_start(self):
        if self.repeats == 1:
            self.interval = self.obj.db.shield['delay']
        if self.interval != 1:
            self.db.msged = False

    def at_repeat(self):
        "called every self.interval seconds."

        # Caching basically every shield variable for easy comparison
        _curr = self.obj.db.shield['current']
        _max = self.obj.db.shield['max']
        _rg = self.obj.db.shield['regen']

        # If delay amount of time has passed since you were last hit, and your shield is lower than the max, regenerate each tick
        self.obj.db.shield['current'] = min(self.obj.db.shield['current'] + _rg, _max)

        if self.db.msged is False:
            _name = self.obj.named()
            self.obj.msg("Your shield glimmers and grows more opaque")
            self.obj.location.msg_contents( ("%s's shield glimmers and grows more opaque." % _name).capitalize(), exclude=self.obj )
            self.db.msged = True

        if _curr >= _max:
            self.pause()                # If your shield is equal or higher than your max, pause regeneration
            self.interval = self.obj.db.shield['delay']
        elif self.interval != 1:
            self.restart(interval=1, repeats=0)    # Otherwise, start over with a 1s interval (shield tick rate) and infinite repeats
            
