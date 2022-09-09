from typeclasses.context import Context
from evennia.contrib.rpg.buffs.buff import BaseBuff
import content.bufflist as bl


class RampagePerk(BaseBuff):
    key = "rampage"
    name = "Rampage"
    flavor = "Kills with this weapon temporarily increase its damage."

    trigger = "hit"

    def on_trigger(self, trigger, *args, **kwargs):
        self.owner.buffs.add(bl.RampageBuff)


class ExploitPerk(BaseBuff):

    key = "exploit"
    name = "Exploit"
    flavor = "Shooting an enemy with this weapon allows you to find their weakness."

    trigger = "hit"

    stack_msg = {
        1: "    You begin to notice flaws in your opponent's defense.",
        10: "    You're certain you've found a weakness. You just need more time.",
        20: "    You've discovered your opponent's weak spot.",
    }

    trigger_msg = ""

    def on_trigger(self, trigger, *args, **kwargs):
        if self.owner.buffs.find(bl.Exploited):
            return None
        self.owner.buffs.add(bl.Exploit)
        if self.stacks in self.stack_msg:
            self.owner.location.msg(self.stack_msg[self.stacks])


class WeakenPerk(BaseBuff):
    key = "weaken"
    name = "Weaken"
    flavor = "Shooting an enemy with this weapon applies a virulent poison."

    trigger = "hit"

    def on_trigger(self, trigger, defender, *args, **kwargs):
        defender.buffs.add(bl.Poison)


class LeechRoundPerk(BaseBuff):
    key = "leechround"
    name = "Leech Round"
    flavor = "Primes enemies with a leeching worm which heals attackers."

    trigger = "hit"

    def on_trigger(self, trigger, defender, *args, **kwargs):
        defender.buffs.add(bl.Leeching)


class ThornsPerk(BaseBuff):
    key = "thorns"
    name = "Thorns"
    flavor = "Damages attackers"

    trigger = "injury"

    def on_trigger(self, trigger, attacker, damage, *args, **kwargs):
        attacker.damage(damage * 0.1)


class PerkList:
    rampage = RampagePerk
    exploit = ExploitPerk
    weaken = WeakenPerk
    leechround = LeechRoundPerk
