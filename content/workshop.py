"""Where new perks and buffs are made!"""

from evennia.contrib.rpg.buffs.buff import BaseBuff, Mod


class FourthTime(BaseBuff):
    id = "fourthtime"
    name = "Fourth Time's The Charm"
    flavor = "Rapidly landing precision hits returns two rounds to the magazine."

    trigger = "crit"

    def on_trigger(self, *args, **kwargs):
        self.owner.buffs.add(FourthTimeEffect)


class FourthTimeEffect(BaseBuff):
    id = "fourthtime"
    name = "Fourth Time's The Charm"
    flavor = "Rapidly landing precision hits returns two rounds to the magazine."

    duration = 30
    maxstacks = 4

    trigger = "crit"

    def on_trigger(self, *args, **kwargs):
        if self.stacks >= 4:
            self.owner.location.msg("Your magazine feels slightly heavier.")
            self.owner.db.ammo += 2
            self.remove()


class RapidHit(BaseBuff):
    id = "rapidhit"
    name = "Rapid Hit"
    flavor = "Precision hits temporarily increase stability and reload speed."

    trigger = "crit"

    def on_trigger(self, *args, **kwargs):
        pass


class RapidHitBuff(BaseBuff):

    id = "rapidhit"
    name = "Rapid Hit"
    flavor = "Precision hits temporarily increase stability and reload speed."

    duration = 30
    refresh = True
    stacking = True

    maxstacks = 5

    mods = [Mod("stability", "add", 6, 1), Mod("reload", "mult", -0.05, -0.05)]


class KillClipPerk(BaseBuff):
    id = "kc_perk"
    name = "Kill Clip"
    flavor = "Reloading after a kill grants increased damage."

    trigger = "kill"

    def on_trigger(self, *args, **kwargs):
        self.owner.buffs.add(KillClipEffect)


class KillClipEffect(BaseBuff):
    id = "kc_triggered"
    name = "Kill Clip"
    flavor = "Reloading after a kill grants increased damage"

    trigger = "reload"

    duration = 30

    def on_trigger(self, *args, **kwargs):
        self.owner.location.msg("Your weapon begins to glow with otherworldly light.")
        self.owner.buffs.add(KillClipBuff)


class KillClipBuff(BaseBuff):
    id = "killclip"
    name = "Kill Clip"
    flavor = "Reloading after a kill grants increased damage."

    duration = 300

    refresh = False
    stacking = False
    unique = True

    mods = [Mod("damage", "mult", 0.25, 0.0)]

    def on_remove(self, *args, **kwargs):
        pass
