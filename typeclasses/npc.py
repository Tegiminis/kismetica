from evennia.utils.utils import lazy_property
from typeclasses.characters import Character
from typeclasses.components.ai import AIHandler


import random


class NPCWeapon:
    name = "Template"

    accuracy = 1.0
    damage = 10
    crit = 2.0
    mult = 2.0
    spread = 1.0
    mult = 1.0

    element = "neutral"
    msg = "%s shoots %s with %s."
    cooldown = 6

    def __init__(
        self, name, accuracy, damage, crit, mult, spread, combo, element, msg, cooldown
    ) -> None:

        self.name = name
        self.accuracy = accuracy
        self.damage = damage
        self.crit = crit
        self.mult = mult
        self.spread = spread
        self.combo = combo
        self.element = element
        self.msg = msg
        self.cooldown = cooldown

    @property
    def WeaponData(self):
        dict = {
            "damage": random.randint(self.damage * 0.5, self.damage * 1.5),
            "critChance": self.crit,
            "critMult": self.mult,
            "accuracy": self.accuracy,
            "spread": self.spread,
            "shots": self.shots,
        }


class NPC(Character):
    @lazy_property
    def ai(self) -> AIHandler:
        return AIHandler(self)

    def at_object_creation(self):
        super().at_object_creation()

        # Various types of messaging
        self.db.msg = {
            "idle": [
                "%s stomps their feet impatiently." % self.named,
                "%s bares their teeth menacingly." % self.named,
            ],
            "despawn": "%s crumbles away into a fine dust." % self.named,
            "respawn": "%s revives in a glittering beam of light." % self.named,
            "retreat": "%s backs up to find a better position." % self.named,
        }

        self.db.lootable = True  # Can this mob be looted?

        # Various AI timers and things
        self.db.timer = {
            "idle": 5,
            "search": 3,  # How long after searching before thinking again
            "attack": 3,  # How long after attacking before thinking again
            "patrol": 3,  # How long after patrolling before thinking again
            "dead": 30,  # How long this AI remains dead before it respawns
            "respawn": 10,  # How long after respawn before thinking again
        }

        # The template weapon for all NPCs.
        self.db.weapon = NPCWeapon

        self.db.range = 4

        # States for the state machine
        self.db.state = "active"

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
        self.location.msg_contents("Debug: Hunting target to nearby rooms")

        exits = self.find_exits()
        self.location.msg_contents("Debug: Hunting exits found %s" % exits)
        dest = None
        if exits:
            # scan the exit destinations for targets
            for exi in exits:
                targets = self.find_targets(exi.destination)
                if targets != None:  # If targets were found
                    if (
                        target in targets
                    ):  # If existing target is found in the room, set it as your next destination
                        dest = exi
                elif (
                    targets == None
                ):  # If no targets were found, return None (typically, return to patrol)
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

    def npc_attack(self, defender):
        """
        Attacks the specified target with the NPC's default weapon
        The most basic form of attack an NPC can do.
        """
        weapon: NPCWeapon = self.db.weapon
        combat = {"attacker": self, "defender": defender}

        self.location.msg_contents("Debug: Attacking a target in this room.")

        weapon_stats = weapon.WeaponData
        combat = self.single_attack(defender, *weapon_stats, context=combat)

        self.location.msg_contents(
            f"Hit: {combat.hit} | Crit: {combat.crit} | Damage: {combat.damage}"
        )

        if combat.hit:
            defender.damage(combat.damage, context=combat)
            msg_damage = f"{combat.damage} damage!"
        else:
            msg_damage = "Miss!"

        defender.msg(
            ("\n|n" + (weapon.msg % (self.name, "you", weapon.name)).capitalize())
            + ("\n|n" + msg_damage)
        )

        self.location.msg_contents(
            (
                "\n|n"
                + (weapon.msg % (self.name, defender.named, weapon.name)).capitalize()
            )
            + ("\n|n" + msg_damage),
            exclude=(self, defender),
        )
