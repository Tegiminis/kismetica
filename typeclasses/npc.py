from components.context import congen
from evennia.utils.utils import lazy_property
from typeclasses.characters import Character
from components.ai import BrainHandler, PatrolBrain, TestBrain
from dataclasses import dataclass
import random
from components.combat import WeaponStats

DEFAULT_NPC_MESSAGING = {
    "think": "{owner} looks lost in thought.",
    "hunt": "",
    "target": "",
}


@dataclass
class NPCWeapon(WeaponStats):
    pass


class NPC(Character):
    @lazy_property
    def ai(self) -> BrainHandler:
        return BrainHandler(self)

    @property
    def weapon(self) -> NPCWeapon:
        return self.db.weapon

    def at_object_creation(self):
        super().at_object_creation()

        # The template weapon for all NPCs.
        self.db.weapon = NPCWeapon

        # XP gained on killing this enemy
        self.db.gain = 10

        self.db.messaging = {}

        self.db.brain = TestBrain

    def at_init(self):
        _ai = self.ai
        return super().at_init()

    def find_targets(self, location):
        """
        Find all potential targets in the specified room.
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
        self.location.msg_contents("Debug: Hunting target to nearby rooms")

        exits = self.find_exits()
        self.location.msg_contents("Debug: Hunting exits found %s" % exits)
        dest = None
        if exits:
            # scan the exit destinations for targets
            for exi in exits:
                targets = self.find_targets(exi.destination)
                if targets != None:  # If targets were found
                    if target in targets:
                        dest = exi
                elif targets == None:
                    dest = None
                    self.location.msg_contents("Debug: No hunting target found")
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

    def npc_attack(self, defender: Character):
        """
        Attacks the specified target with the NPC's default weapon
        The most basic form of attack an NPC can do.
        """
        weapon = self.db.weapon
        if not isinstance(self.db.weapon, WeaponStats):
            weapon: WeaponStats = weapon()

        weapon.damage = random.randint(
            round(weapon.damage * 0.5), round(weapon.damage * 1.5)
        )
        self.combat.weapon_attack(weapon, defender)
