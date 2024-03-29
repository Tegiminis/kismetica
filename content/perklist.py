from evennia.contrib.rpg.buffs.buff import BaseBuff
import content.bufflist as bl


class RampagePerk(BaseBuff):
    key = "rampage"
    name = "Rampage"
    flavor = "Kills with this weapon temporarily increase its damage."

    triggers = ["hit"]

    def at_trigger(self, trigger, *args, **kwargs):
        self.owner.buffs.add(bl.RampageBuff, source=self.owner)


class ExploitPerk(BaseBuff):
    key = "exploit"
    name = "Exploit"
    flavor = "Shooting an enemy with this weapon allows you to find their weakness."

    triggers = ["hit"]

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
        defender.buffs.add(bl.Poison, source=self.owner.location)


class LeechRoundPerk(BaseBuff):
    key = "leechround"
    name = "Leech Round"
    flavor = "Primes enemies with a leeching worm which heals attackers."

    triggers = ["hit"]

    def at_trigger(self, trigger, defender, *args, **kwargs):
        defender.buffs.add(bl.Leeching, source=self.owner.location)


class ThornsPerk(BaseBuff):
    key = "thorns"
    name = "Thorns"
    flavor = "Damages attackers"

    triggers = ["injury"]

    def at_trigger(self, trigger, attacker, total, *args, **kwargs):
        thorns = round(total * 0.1)
        if not thorns:
            return
        attacker.combat.injure(thorns, loud=False, event=False, attacker=attacker)
        attacker.msg("You take {dmg} thorns damage!".format(dmg=thorns))


class PerkList:
    rampage = RampagePerk
    exploit = ExploitPerk
    weaken = WeakenPerk
    leechround = LeechRoundPerk
