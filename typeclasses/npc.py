from typeclasses.characters import Character

# destiny_rules is the rules module that contains all combat calculations, enums, and other important doodads
from world import destiny_rules

import random

class NPC(Character):
    
    def at_object_creation(self):
        super().at_object_creation()
        
        # Various types of messaging
        self.db.msg = {
            'idle': [
                "%s stomps their feet impatiently." % self.named(),
                "%s bares their teeth menacingly." % self.named()
            ],
            'despawn': "%s crumbles away into a fine dust." % self.named(),
            'advance': "%s lumbers forward, stomping the ground with chitinous feet." % self.named(),
            'respawn': '%s revives in a glittering beam of light.' % self.named(),
            'retreat': "%s backs up to find a better position." % self.named()
        }

        self.db.lootable = True     # Can this mob be looted?

        # Various AI timers and things
        self.db.timer = {
            'idle': 5,
            'search': 3,            # How long after searching before thinking again
            'attack': 3,            # How long after attacking before thinking again
            'patrol': 3,            # How long after patrolling before thinking again
            'dead': 30,             # How long this AI remains dead before it respawns
            'respawn': 10           # How long after respawn before thinking again
        }

        # The basic ranged attack for all NPCs.
        self.db.basic_ranged = {
            'name':'Hive Boomer',
            'element':'arc',
            'damage':20,
            'acc': 1.5,
            'msg': '%s shoots %s with a %s.',
            'cooldown': 6

        }

        # The range the NPC always sits at. You suffer an accuracy penalty shooting at enemies outside your range
        self.db.range = 2

        # States for the state machine
        self.db.state = 'active'

        # The AI's current target
        self.db.target = None
    
    def find_targets(self, location):
        """
        Find all potential targets in the current room.
        """
        targets = [
            obj
            for obj in location.contents_get(exclude=self)
            if obj.has_account and not obj.is_superuser
        ]
        return targets if targets else None

    def find_exits(self):
        """
        Find all valid exits to the current location.
        """
        exits = [exi for exi in self.location.exits if exi.access(self, "traverse")]
        return exits
    
    def hunt(self, target):
        """
        Search nearby rooms for the specified target. If no
        target is specified, search nearby rooms for any target.

        Returns: Destination of existing or new target
        """
        self.location.msg_contents('Debug: Hunting target to nearby rooms')
        
        exits = self.find_exits()
        self.location.msg_contents('Debug: Hunting exits found %s' % exits)
        dest = None
        if exits:
            # scan the exit destinations for targets
            for exi in exits:
                targets = self.find_targets(exi.destination)
                if targets != None:             # If targets were found
                    if target in targets:           # If existing target is found in the room, set it as your next destination
                        dest = exi
                elif targets == None:           # If no targets were found, return None (typically, return to patrol)
                    dest = None
                    self.location.msg_contents('Debug: No hunting target found')
        return dest
    
    def patrol_move(self):
        """
        Scan the current room for exits, and randomly pick one.
        """
        # target found, look for an exit.
        exits = self.find_exits()
        if exits:
            if len(exits) == 1:
                self.move_to(exits[0].destination)
            else:
                self.move_to(random.choice(exits).destination)
        else:
            # no exits! teleport to home to get away.
            self.move_to(self.home)
    
    def npc_attack(self, target):
        """
        Attacks the specified target with the NPC's default weapon
        The most basic form of attack an NPC can do.
        """
        weapon = self.db.basic_ranged
        damage = 0
        msg_damage = ''

        chance_hit = random.random()
        hit_roll = random.random()

        if chance_hit >= hit_roll:
            damage = weapon['damage']
            destiny_rules.damage_target(damage, None, target)
            msg_damage = "%s damage!" % str(damage)
        elif chance_hit < hit_roll:
            msg_damage = "Miss!"

        target.msg(
            ( "\n|n" + (weapon['msg'] % (self.named(), 'you', weapon['name'])).capitalize() ) +
            ( "\n|n" + msg_damage )
        )

        self.location.msg_contents(
            ( "\n|n" + (weapon['msg'] % (self.named(), target.named(), weapon['name'])).capitalize() ) +
            ( "\n|n" + msg_damage ), 
            exclude=(self, target)
        )