import random
from evennia.contrib.rpg.buffs.buff import BaseBuff, Mod


class RampageBuff(BaseBuff):
    key = "rampage"
    name = "Rampage"
    flavor = "Defeating an enemy has filled you with bloodlust."

    duration = 30

    refresh = True
    stacking = True
    unique = True
    maxstacks = 3

    stack_msg = {
        1: "    You feel a bloodlust welling up inside you.",
        2: "    Your bloodlust calls to you.",
        3: "    All must die.",
    }

    mods = [Mod("damage", "mult", 0.15, 0.15)]

    def at_apply(self, *args, **kwargs):
        if self.stacks in self.stack_msg.keys():
            self.owner.msg(self.stack_msg[self.stacks])

    def at_expire(self, *args, **kwargs):
        self.owner.location.msg("The bloodlust fades.")


class Exploit(BaseBuff):
    key = "exploit"
    name = "Exploit"
    flavor = "You are learning your opponent's weaknesses."

    triggers = ["hit"]

    duration = 30

    refresh = True
    stacking = True
    unique = True
    maxstacks = 20

    def at_trigger(self, trigger: str, *args, **kwargs):
        chance = self.stacks / 20
        roll = random.random()

        if chance > roll:
            self.owner.buffs.add(Exploited)
            self.owner.location.msg("   An opportunity presents itself!")
            self.owner.buffs.remove("exploit")

    def at_expire(self, *args, **kwargs):
        self.owner.location.msg("The opportunity passes.")


class Exploited(BaseBuff):
    key = "exploited"
    name = "Exploited"
    flavor = "You have sensed your target's vulnerability, and are poised to strike."

    duration = 30

    refresh = True
    stacking = False
    unique = True

    mods = [Mod("damage", "add", 100)]

    def at_post_check(self, *args, **kwargs):
        self.owner.location.msg("   You exploit your target's weakness!")
        self.owner.buffs.remove("exploited", delay=0.01)

    def at_remove(self, *args, **kwargs):
        self.owner.location.msg("You cannot sense your target's weakness anymore.")


class Weakened(BaseBuff):
    key = "weakened"
    name = "Weakened"
    flavor = "An unexplained weakness courses through this person."

    duration = 30

    refresh = True
    stacking = False
    unique = True

    mods = [Mod("injury", "add", 100)]


class Leeching(BaseBuff):
    key = "leeching"
    name = "Leeching"
    flavor = "Attacking this target fills you with vigor."

    duration = 30

    refresh = True
    stacking = False
    unique = True

    triggers = ["injury"]

    def at_trigger(self, trigger: str, attacker, damage, *args, **kwargs):
        if not attacker or not damage:
            return
        attacker.msg("Debug: Attempting leech.")
        heal = damage * 0.1
        attacker.heal(heal)


class Poison(BaseBuff):
    key = "poison"
    name = "Poison"
    flavor = "A poison wracks this body."

    duration = 30

    refresh = True
    unique = True
    playtime = True

    maxstacks = 5
    tickrate = 5

    cache = {"damage": 5}

    def at_pause(self, *args, **kwargs):
        self.owner.db.prelogout_location.msg_contents(
            "{actor} stops twitching, their flesh a deathly pallor.".format(
                actor=self.owner
            )
        )

    def at_unpause(self, *args, **kwargs):
        self.owner.location.msg_contents(
            "{actor} begins to twitch again, their cheeks flushing red with blood.".format(
                actor=self.owner
            )
        )

    def at_tick(self, initial=True, *args, **kwargs):
        _dmg = self.damage * self.stacks
        if initial:
            self.owner.msg("Initial poison tick")
        if not initial:
            self.owner.location.msg_contents(
                "Poison courses through {actor}'s body, dealing {damage} damage.".format(
                    actor=self.owner, damage=_dmg
                )
            )
            self.owner.combat.damage(_dmg, quiet=True)
            self.damage += 1


class Overflow(BaseBuff):
    key = "overflow"
    name = "Overflow"
    flavor = "Your magazine is overflowing!"


class PropertyBuffTest(BaseBuff):
    key = "ptest"
    name = "ptest"
    flavor = "This person is invigorated."

    duration = 600
    playtime = True

    refresh = True
    maxStacks = 5
    unique = True

    mods = [Mod("maxhp", "add", 100, 50)]


class TestLongTicker(BaseBuff):
    key = "longtick"


class TestBuff(BaseBuff):
    key = "ttest"
    name = "ttest"
    flavor = "This buff has been triggered."

    triggers = ["test"]

    def at_trigger(self, trigger: str, *args, **kwargs):
        print("Triggered test buff!")


class Invulnerable(BaseBuff):
    key = "invuln"
    name = "Invulnerable"
    flavor = "This character is immune to damage"

    mods = [Mod("injury", "custom", 0)]

    def custom_modifier(self, value, *args, **kwargs):
        _value = value
        _value *= 0
        return _value


class BuffList:
    """Initialization of buff and effect typeclasses used to apply buffs to players.

    If it's not in this list, it won't be applicable in-game without python access."""

    # Buffs
