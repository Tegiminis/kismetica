import random
from random import randint
from typeclasses import characters as Character
from evennia import utils
import time

slot = {'kinetic':0 , 'energy':1 , 'power':2}
element = {'neutral':0 , 'void':1 , 'solar':2, 'arc':3}
ammo = {'primary':0 , 'special':1 , 'power':2}
armor = {'head':0 , 'arms':1 , 'chest':2, 'legs':3, 'class':4}

def roll_hit(origin, target):
    """
    Rolls to hit a target. This function requires the target to have a ranged weapon.
    
    Args:
        origin: The attacker.
        target: The defender

    Returns a tuple: was it a
    """
    # Get the weapon used, required for a good portion of the hit calculation
    slot = origin.db.equipped_held
    weapon = origin.db.equipped_weapons[slot]
    weapon_acc = weapon.ndb.acc
    chance_crit = weapon.db.crit['chance']

    # Find the distance between the attacker and the target's room_depth
    dist = distance(origin, target)

    # For accuracy calculations, we use range_max. 
    # At max range, you are incapable of hitting your target ever.
    # At half range, you have to be very unlucky to miss 
    # At point blank range, you cannot miss.
    range_max = weapon.db.range['max']
    if range_max - dist > 0.0:
        range_acc = 2.0 * (range_max - dist) / range_max
    else:
        range_acc = 0.0

    # Random values for hit calculations
    # hit_roll must be > hit_chance for the player to hit
    chance_hit = random.random()
    hit_roll = random.random()

    # Modify the hit roll by the weapon's accuracy and the distance between targets
    # 1.0 is unchanged roll
    # 0.0 is guaranteed miss
    # Higher is better
    hit_roll = hit_roll * weapon_acc * range_acc

    return (hit_roll > chance_hit, hit_roll > chance_hit * chance_crit)

def combat_damage(origin, target, hit, crit):
    ###
    # Damages the target based on the caller's weapon and a bunch of damage calculations.
    # Damage is modified by:
    # - Precision damage multiplier
    # - Element type
    # - Damage falloff
    ###

    if hit is False:
        return 0

    slot = origin.db.equipped_held
    weapon = origin.db.equipped_weapons[slot]
    damage = weapon.db.damage['base']
    ele_wep = weapon.db.element
    ele_tar = target.db.shield['element']

    # Neutral (aka physical) element damage does extra damage to normal shields and health
    if ele_wep == 'neutral':
        if ele_tar == 'neutral' or target.db.shield['current'] <= 0:
            damage = round(damage * 1.05)

    # All elemental damage deals increased damage to enemies with any elemental shields
    # More damage if the elements match
    else:
        if ele_wep == ele_tar:
            damage = round(damage * 1.2)
        elif ele_tar != 'neutral':
            damage = round(damage * 1.05)

    # All damage is multiplied by crit
    if crit is True:
        damage = round(damage * weapon.db.crit['mult'])

    return damage

def damage_target(damage, target):
    # Actually does the nitty gritty of damaging your target
    now = time.time()
    t_shield = target.db.shield['current']

    # If the shield value is less than the damage dealt, deal it to both health and shields. Otherwise, just shields.
    if damage > target.db.shield['current']:
        t_shield = target.db.shield['current']
        target.db.shield['current'] = 0
        damage -= t_shield
        target.db.health['current'] -= damage
    else:
        target.db.shield['current'] -= damage

    # If the target has a shield, then trigger shield regeneration
    if target.db.shield['max'] > 0:
        target.db.shield['lasthit'] = now
        _sc = target.scripts.get('shield_regen')
        _sc[0].unpause()
        _sc[0].db.msged = False

    if target.db.health['current'] <= 0:
        kill(target)

    return

def kill(origin):
    # Kills whatever object is called for the function
    if utils.inherits_from(origin, 'typeclasses.npc.NPC'):
        origin.db.npc_active = False

    _sc = origin.scripts.get('shield_regen')
    _sc[0].pause()

    return

def revive(origin):
    # Revives the object called for the function
    if utils.inherits_from(origin, 'typeclasses.npc.NPC'):
        origin.db.health['current'] = origin.db.health['max']
        origin.db.npc_active = True
    origin.location.msg_contents("The %s revives in a glimmering beam of light." % origin.name)
    _sc = origin.scripts.get('shield_regen')
    _sc[0].unpause()
    _sc[0].db.msged = False
    return

def distance(origin, target):
    # Finds the distance between the room_depths of two objects
    start = origin.db.room_depth
    end = target.db.room_depth

    return abs(origin.db.room_depth - target.db.room_depth)