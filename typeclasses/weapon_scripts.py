import random
import time
from typeclasses.scripts import Script
from evennia import utils

class Rampage(Script): 
    """
    A buff which increases your damage 
    """
    def at_script_creation(self):
        self.key = "rampage"
        self.desc = "Increases damage by multiplier"
        self.interval = 5           # Amount of time until buff falls off
        self.persistent = True      # Will survive reload
        self.start_delay = True

        self.tags.add( 'kill' )

        self.db.mult = 0.25
        self.db.stacks = 0
        self.db.stacks_max = 3

        self.db.msg = {
            'start': '|gRampage stack x%i',
            'end': 'Rampage falls off.'
        }

        # If this script is on anything but a weapon, it will be removed on start
        if utils.inherits_from(self.obj, 'typeclasses.weapon.Weapon') is False:
            self.obj.scripts.delete(self)

        self.pause()

    def at_start(self):
        if self.db.stacks < self.db.stacks_max:
            self.obj.db.damage['mult'] += self.db.mult
        self.db.stacks = min( self.db.stacks + 1, self.db.stacks_max )
        self.db.msg['start'] = self.db.msg['start'] % self.db.stacks

    def at_repeat(self):
        "called every self.interval seconds."
        self.obj.db.damage['mult'] -= self.db.mult * self.db.stacks     # Remove the multiplier buff from your weapon
        self.db.stacks = 0                                              # If this script's timer ever finishes, it immediately resets your multiplier
        self.obj.location.msg( self.db.msg['end'] )
        self.pause()