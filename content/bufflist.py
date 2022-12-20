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

    stack_msg = {
        1: "    You begin to notice flaws in your opponent's defense.",
        3: "    You're certain you've found a weakness. You just need more time.",
        5: "    You've discovered your opponent's weak spot.",
    }

    def at_apply(self, *args, **kwargs):
        if self.stacks in self.stack_msg:
            self.owner.location.msg(self.stack_msg[self.stacks])

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

    mods = [Mod("total_damage", "add", 100)]

    def at_post_check(self, *args, **kwargs):
        self.owner.location.msg("      + You exploit your target's weakness!")
        self.owner.buffs.remove("exploited")


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

    def at_trigger(self, trigger: str, attacker, total, *args, **kwargs):
        if not (attacker and total):
            return
        heal = round(total * 0.1)
        attacker.combat.heal(heal)


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
        _s = str(self.cache)
        poison = self.damage * self.stacks
        if not initial:

            # self.owner.location.msg_contents("Debug: buff cache - " + _s)
            self.owner.combat.injure(
                poison, attacker=self.source, buffcheck=False, event=False
            )
            mesg = "Poison courses through {actor}'s body, dealing {damage} damage."
            self.owner.location.msg_contents(
                mesg.format(actor=self.owner, damage=poison)
            )
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
