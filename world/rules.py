import random
import time
from evennia import utils


def make_context(context: dict = None):
    """Boilerplate for either creating a new context or setting one up."""
    if not context:
        context = {}
    else:
        context = dict(context)
    return context


def basic_attack(attacker, defender):
    """The most basic attack a player can perform. Uses a weapon, held by origin, to attack the target.

    Attacker must have a weapon in db.held, otherwise this command will return an error.
    """

    # The context for our combat.
    # This holds all sorts of useful info we pass around.
    combat = Context(attacker, defender)

    combat.weapon = attacker.db.held
    weapon = combat.weapon

    # Variable assignments for legibility
    rpm = combat.weapon.rpm

    # If it has been too soon since your last attack, or you are attacking an invalid target, stop attacking
    if attacker.cooldowns.isActive("attack") or not defender.is_typeclass(
        "typeclasses.npc.NPC"
    ):
        attacker.msg("You cannot act again so quickly!")
        return

    # The string of "hits" used for messaging.
    damage_message = ""

    # Hit calculation and context update
    hit = roll_hit(attacker, defender)
    combat.hit = hit[0]
    combat.crit = hit[1]

    attacker.msg(
        (combat.weapon.db.msg["attack"] % ("you", defender.named)).capitalize()
    )
    if hit[1]:
        damage_message += "|yCrit! "

    # Damage calculation and messaging
    combat.damage = calculate_damage(attacker, defender, *hit)
    damage_message += "%i damage!" % combat.damage

    if combat.hit:
        defender.damage(combat.damage)
        attacker.msg(damage_message + "\n|n")

        weapon.buffs.trigger("hit", context=combat)
        attacker.buffs.trigger("hit", context=combat)

        if combat.crit:
            weapon.buffs.trigger("crit", context=combat)
            attacker.buffs.trigger("crit", context=combat)

        defender.buffs.trigger("thorns", context=combat)
        defender.buffs.trigger("injury", context=combat)
    else:
        attacker.msg(weapon.db.msg["miss"])

    attacker.cooldowns.start("attack")
    utils.delay(rpm, basic_attack, attacker=attacker, defender=defender)


def roll_hit(attacker, defender):
    """
    Rolls to hit a defender. This function requires the attacker to have a weapon.

    Args:
        attacker: The attacker.
        defender: The defender.

    Returns a tuple of bools: was hit, and was crit
    """
    # Get the weapon used, required for a good portion of the hit calculation
    weapon: Weapon = attacker.db.held

    # Apply all accuracy and crit buffs for attack, and evasion buffs for defense
    accuracy = weapon.accuracy
    accuracy = attacker.buffs.check(accuracy, "accuracy")
    crit = weapon.critChance
    crit = attacker.buffs.check(crit, "crit")
    evasion = defender.evasion
    evasion = defender.buffs.check(evasion, "evasion")

    # Apply a range penalty equal to 20% times the difference in defender and attacker range
    range_penalty = 1.0
    if defender.db.range < weapon.cqc:
        range_penalty -= 0.2 * abs(weapon.cqc - defender.db.range)

    # Random values for hit calculations
    # hit must be > evasion for the player to hit
    hit = random.random()
    dodge = random.random()
    # attacker.msg('Debug rolls: Hit %f | Dodge %f' % (hit, dodge))

    # Modify the hit roll by the accuracy value.
    hit = hit * accuracy
    dodge = dodge * evasion
    # attacker.msg('Debug modified rolls: Hit %f | Dodge %f' % (hit, dodge))

    return (hit > dodge, hit > dodge * crit)


def calculate_damage(attacker, defender, hit, crit) -> float:
    """Calculates damage against a defender."""

    if hit is False:
        return 0.0

    weapon: Weapon = attacker.db.held

    # Roll to find damage based on weapon's min/max, and apply weapon buffs
    # attacker.msg('Debug Base Damage: ' + str(weapon.db.damage))
    damage = weapon.damage

    # Apply falloff, if relevant. Falloff is a flat 20% damage penalty
    if weapon.falloff < defender.db.range:
        damage *= 0.8

    # All damage is multiplied by crit
    if crit is True:
        damage = round(damage * weapon.critMult)

    # attacker.msg('Crit Damage: ' + str(damage))

    # Apply all attacker buffs to damage
    damage = attacker.buffs.check(damage, "damage")
    # attacker.msg('Debug Attacker-modified Damage: ' + str(damage))

    # Apply all defender buffs to damage
    damage = defender.buffs.check(damage, "injury")
    # attacker.msg('Debug Defender-modified Damage: ' + str(damage))

    attacker.buffs.cleanup()
    defender.buffs.cleanup()

    return round(damage)


def damage_target(damage, target):

    # Damage the target's health
    target.db.health -= damage

    # If the target has 0 health, kill it
    # if target.db.health <= 0:
    #     kill(target)

    return


def kill(origin):
    # Kills whatever object is called for the function
    # if utils.inherits_from(origin, 'typeclasses.npc.NPC'):
    # origin.db.state = 'dead'
    # for x in find_scripts_by_tag(origin, 'ai'):
    #     x.restart( interval=origin.db.timer['dead'], start_delay=True )
    pass


def revive(origin):
    origin.location.msg_contents("Debug: Revival started")

    # Revives the object called for the function
    if hasattr(origin, "health"):
        origin.db.health = origin.db.health["max"]


def find_scripts_by_tag(obj, tag):
    _list = [x for x in obj.scripts.all() if tag in x.tags.all()]

    return _list


def check_time(start, end, duration):
    """Check to see if duration time has passed between the start and end time.
    Used for checking cooldowns or buff timing.

    Always returns false if duration is -1 (for things that last forever)."""

    if duration == -1 or not (duration and start and end):
        return False
    if duration < end - start:
        return True
    else:
        return False
