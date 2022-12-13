from evennia.contrib.rpg.buffs.buff import BaseBuff
import content.bufflist as bl


class RampagePerk(BaseBuff):
    key = "rampage"
    name = "Rampage"
    flavor = "Kills with this weapon temporarily increase its damage."

    triggers = ["hit"]

    def at_trigger(self, trigger, *args, **kwargs):
        self.owner.buffs.add(bl.RampageBuff)


class ExploitPerk(BaseBuff):
    key = "exploit"
    name = "Exploit"
    flavor = "Shooting an enemy with this weapon allows you to find their weakness."

    triggers = ["hit"]

    trigger_msg = ""

    def at_trigger(self, trigger, *args, **kwargs):
        if self.owner.buffs.has(bl.Exploited):
            return None
        self.owner.buffs.add(bl.Exploit)


class WeakenPerk(BaseBuff):
    key = "weaken"
    name = "Weaken"
    flavor = "Shooting an enemy with this weapon applies a virulent poison."

    triggers = ["hit"]

    def at_trigger(self, trigger, defender, *args, **kwargs):
        defender.buffs.add(bl.Poison)


class LeechRoundPerk(BaseBuff):
    key = "leechround"
    name = "Leech Round"
    flavor = "Primes enemies with a leeching worm which heals attackers."

    triggers = ["hit"]

    def at_trigger(self, trigger, defender, *args, **kwargs):
        defender.buffs.add(bl.Leeching)


class ThornsPerk(BaseBuff):
    key = "thorns"
    name = "Thorns"
    flavor = "Damages attackers"

    triggers = ["injury"]

    def at_trigger(self, trigger, attacker, damage_taken, *args, **kwargs):
        _context = {
            "attacker": self.owner,
            "defender": attacker,
            "damage_taken": damage_taken,
        }
        _up = dict(kwargs)
        _context.update(_up)
        thorns = round(damage_taken * 0.1)
        if not thorns:
            return
        attacker.combat.take_damage(
            thorns, loud=False, source=attacker, context=_context
        )
        attacker.msg("You take {dmg} thorns damage!".format(dmg=thorns))


class PerkList:
    rampage = RampagePerk
    exploit = ExploitPerk
    weaken = WeakenPerk
    leechround = LeechRoundPerk
