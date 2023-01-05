from components.context import congen
from evennia.utils.utils import lazy_property
from typeclasses.characters import Character
from components.ai import BrainHandler, PatrolBrain, TestBrain
from dataclasses import dataclass, replace
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
        self.ai.act()
        return super().at_init()

    def npc_attack(self, defender: Character):
        """
        Attacks the specified target with the NPC's default weapon
        The most basic form of attack an NPC can do.
        """
        # get our static weapon (db dictionary)
        weapondict = dict(self.db.weapon)
        print(weapondict)

        # turn it into weapon stats
        weapon = WeaponStats(**weapondict)
        weapon.damage = random.randint(
            round(weapon.damage * 0.5), round(weapon.damage * 1.5)
        )
        self.combat.weapon_attack(weapon, defender)
