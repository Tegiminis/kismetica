import time
import buffhandler as BH
from objects import Object, DefaultObject

class Buff():
    
    uid = None      # Unique ID, randomly generated at buff application
    pid = None      # Parent ID, reference to the parent script that applied the buff (used in buff removal)

    stat = ''       # The stat the buff affects. Should be a string like so: damage.base
    stacks = 0      # How many stacks of the buff there are (default: 1)
    duration = 0    # Amount of time the buff sticks around
    time = 0        # Time the buff was added
    base = 0        # The base value of the stat change
    perstack = 0    # The value added per stack
    eff = None      # The type of effect a buff has on a stat