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
            'msg': '%s shoots %s with a %s.',
            'cooldown': 6

        }

        self.db.ideal_range = 30    # Range, in room_depth, that the AI will try to reach before shooting

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
        """
        exits = self.find_exits()
        if exits:
            # scan the exits destination for targets
            for exi in exits:
                targets = self.find_targets(exi.destination)
                if target != None and target in targets:
                    # Target found. Move there.
                    self.move_to(exi.destination)
                    return True
                elif targets:
                    self.db.target = targets[0]
                    self.move_to(exi.destination)
                    return True           
        self.obj.location.msg_contents('Debug: No new targets found, going back on patrol')
        return False
    
    def patrol_move(self):
        """
        Scan the current room for exits, and randomly pick one.
        """
        # target found, look for an exit.
        exits = self.find_exits()
        if exits:
            self.location.msg_contents('Debug: Found an exit! %s' % str(exits))
            if len(exits) == 1:
                self.move_to(exits[0].destination)
            else:
                self.move_to(random.choice(exits).destination)
        else:
            self.location.msg_contents('Debug: No exit found!')
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

        self.location.msg_contents("Debug: Hit Chance %f | Roll: %f" % (chance_hit,hit_roll))

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