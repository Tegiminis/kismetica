import random
import evennia.utils as utils


def shoot(self, defender, auto=True, sim=False):
    """The most basic attack a character can perform.

    Attacker must have a weapon in db.held, otherwise
    this method will return an error.
    """
    if not self.tags.has("attacking", "combat"):
        return

    # Can't attack something that isn't an NPC (for now)
    if self.obj.is_typeclass(
        "typeclasses.characters.PlayerCharacter"
    ) and not defender.is_typeclass("typeclasses.npc.NPC"):
        self.msg("You can only attack NPCs!")
        return

    # Your target changed rooms; gave you the slip
    if defender.location != self.location:
        self.msg("Your target has slipped away from you!")
        return

    weapon = self.db.held

    # Can't fire an empty gun!
    if weapon.ammo <= 0:
        self.msg("Your weapon is out of ammo!")
        return

    # Variable assignments for legibility
    _rpm = weapon.rpm

    # If it has been too soon since your last attack, figure out when you can attack next, and delay to then
    if self.cooldowns.find("attack"):
        _tl = self.cooldowns.time_left("attack")
        utils.delay(_tl, self.basic_attack, defender=defender)
        return

    # Default messages for hits and crits, depending on the damage type
    # (bullet, plasma, slashing, blunt)
    default_msg = {
        "bullet": {
            "hit": ["%s staggers under the flurry of bullets.", None],
            "crit": [
                "Blood spurts uncontrollably from newly-apportioned wounds!",
                None,
            ],
        },
        "fusion": {
            "hit": ["Bolts of multicolored plasma singe %s's armor."],
            "crit": ["Molten matter fuses to flesh as %s screams in agony!"],
        },
    }

    # The context dictionary for combat, used to pass combat event data around to other functions
    combat = {"attacker": self, "defender": defender}

    # Messaging for yourself and the room
    self.msg(weapon.db.msg["self"] % (weapon.named, defender.named))
    self.location.msg_contents(
        weapon.db.msg["attack"] % (self.named, weapon.named, defender.named),
        exclude=self,
    )

    # Multishot loop
    for x in range(max(1, weapon.shots)):

        # Bundle weapon stats and pass them to the "single shot" attack method
        weapon_stats = weapon.WeaponData
        combat = self.single_attack(defender, **weapon_stats, context=combat)

        if x <= 0:
            self.msg(f"  HIT: +{int(combat['hit'])} vs EVA: +{int(combat['dodge'])}")

        if combat["isHit"] is True:
            combat["damage"] = defender.damage(combat["damage"], context=combat)

            weapon.buffs.trigger("hit", context=combat)
            if combat["isCrit"] is True:
                weapon.buffs.trigger("crit", context=combat)

            defender.buffs.trigger("thorns", context=combat)
            defender.buffs.trigger("injury", context=combat)

            if combat["isHit"] is True:
                self.msg("    ... %i damage! |n\n" % combat["damage"])

            msgHit = random.choice(default_msg["bullet"]["hit"])
            msgCrit = random.choice(default_msg["bullet"]["crit"])
        else:
            if x <= 0:
                self.msg("    ... Miss!")
            break

    if msgHit:
        self.msg("    " + (msgHit % defender.named).capitalize() + "|n\n")
    if msgCrit:
        self.msg("    " + msgCrit.capitalize() + "|n\n")

    weapon.db.ammo -= 1
    self.cooldowns.start("attack", _rpm)

    if auto:
        utils.delay(_rpm, self.basic_attack, defender=defender)


def weapon_attack(
    self, defender, damage, critChance, critMult, accuracy, context: dict = {}
):
    """Most basic attacks will be of this variety. Uses weapon stats and characteristics to create combat texture.

    Args:
        defender:   The target you are shooting
        damage:     The source damage value; typically weapon damage
        crit:       Crit chance
        mult:       Crit multiplier
        acc:        Accuracy"""

    # self.location.msg_contents("Debug: Attempting a shot")

    # The context for our combat.
    # This holds all sorts of useful info we pass around.
    if not context:
        combat = {"attacker": self, "defender": defender}
    else:
        combat = context

    evasion = defender.evasion

    # Hit calculation and context update
    combat = self.hit_roll(
        accuracy=accuracy, crit=critChance, evasion=evasion, context=combat
    )

    # Damage calc and buff triggers
    if combat.get("isHit"):
        combat["damage"] = self.mod_damage(damage, combat["isCrit"], critMult, False)

        self.obj.buffs.trigger("hit", context=combat)
        if combat.get("isCrit"):
            self.obj.buffs.trigger("crit", context=combat)

    return combat
