from typing import TYPE_CHECKING
import random
import inflect
import evennia.utils as utils
from world.rules import make_context

if TYPE_CHECKING:
    from typeclasses.characters import Character
    from typeclasses.npc import NPC
    from typeclasses.weapon import Weapon

p = inflect.engine()


class CombatHandler(object):
    owner = None

    def __init__(self, owner) -> None:
        self.owner = owner

    @property
    def hp(self):
        return self.owner.db.hp

    @hp.setter
    def hp(self, value):
        self.owner.db.hp = value

    @property
    def maxhp(self):
        return self.owner.maxhp

    def take_damage(self, damage: int = 0, loud=True, raw=False, context=None) -> dict:
        """Applies damage. Affected by "injury" buffs.

        Args:
            damage: Damage to take
            loud:   Use the default damage message (default: True)
            raw:    Is this "raw" damage (unmodified by buffs)?
            context:    Context to update

        Returns a context dictionary updated with the following values:
            damage_taken:   damage taken after buffs were applied
            is_kill:        did this damage instance kill the target?"""

        context = make_context(context)

        # Apply damage
        damage_taken = damage if damage < self.hp else self.hp
        self.hp = max(self.hp - damage, 0)
        if loud:
            self.owner.msg("  ... You take %i damage!" % damage)

        # If you are out of life, you are out of luck
        is_killing = self.hp <= 0
        if is_killing:
            self.die()

        to_update = {"damage_taken": damage_taken, "is_kill": is_killing}
        context.update(to_update)
        return context

    def die(self, context=None):
        """Die! Marks you as dead."""
        context = make_context(context)
        self.owner.tags.clear(category="combat")
        self.owner.tags.add("dead", category="combat")

    def heal(self, heal: int, msg=None) -> int:
        """Heals you.

        Args:
            heal:   The amount you want to heal for (will be converted to an int)
        """
        self.hp = min(self.hp + heal, self.maxhp)
        self.owner.msg("You healed by %i!" % heal)

    def opposed_hit(self, acc=0.0, eva=0.0, crit=2.0, context: dict = None) -> dict:
        """
        Performs an "opposed hit roll". An example of this would be an accuracy
        vs evasion roll, or an awareness vs spread roll. Each roll is
        d100 + random(acc/eva), and a hit is made if the hit value is higher.

        Args:
            acc:    The attacker's accuracy modifier.(default: 0)
            eva:    The defender's evasion modifier. (default: 0)
            crit:   The attacker's crit modifier (default: 2)
            context:    (optional) The context dictionary you wish to update with this method's values

        Returns a context dictionary updated with the following values:
            hit/dodge:  nested dictionary of {base, bonus, total}
            is_hit:     if this was a hit
            hit_div:    hit total divided by dodge total
        """
        context = make_context(context)

        # Roll two d100s
        hit = int(random.random() * 100)
        dodge = int(random.random() * 100)

        # Add random(accuracy) to the relevant values
        accuracy = acc * random.random()
        evasion = eva * random.random()

        # Update and return the context dictionary
        to_update = {
            "hit": {"base": hit, "bonus": accuracy, "total": round(hit + accuracy)},
            "dodge": {"base": dodge, "bonus": evasion, "total": round(dodge + evasion)},
            "is_hit": (hit + accuracy) > (dodge + evasion),
            "hit_div": (hit + accuracy) / (dodge + evasion),
            "is_crit": hit > dodge * crit,
        }

        # Update the context and return
        context.update(to_update)
        return context

    def mod_damage(self, attacker=None, damage=0, crit=False, prec=1, context=None):
        """Modifies the damage taken before applying it. This is where you modify
        damage based on armor, but not general damage reduction."""
        context = make_context(context)

        if crit:
            damage *= attacker.buffs.check(prec, "precision")

        context["damage"] = damage
        return context
