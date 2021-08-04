import random
from random import randint
from typeclasses import characters as Character
from evennia import utils
import time
import typeclasses.buffhandler as bh
import typeclasses.perkhandler as ph

slot = {'kinetic':0 , 'energy':1 , 'power':2}
element = {'neutral':0 , 'void':1 , 'solar':2, 'arc':3}
ammo = {'primary':0 , 'special':1 , 'power':2}
armor = {'head':0 , 'arms':1 , 'chest':2, 'legs':3, 'class':4}

def roll_hit(origin, target):
    '''
    Rolls to hit a target. This function requires the target to have a ranged weapon.
    
    Args:
        origin: The attacker.
        target: The defender

    Returns a tuple of bools: was hit, and was crit
    '''
    # Get the weapon used, required for a good portion of the hit calculation
    slot = origin.db.held
    weapon = origin.db.weapons[slot]
    accuracy = weapon.db.damage['acc']
    crit = weapon.db.crit['chance']

    # Range is simple
    # Check the weapon's range, and the enemy's range
    # If the weapon's range aligns with the enemy's range, there's no penalty
    # If the range exceeds min/max, suffer an accuracy penalty (currently, 40% penalty)
    wep_range = weapon.db.range
    range_acc = 1.0
    if target.db.range < wep_range['min'] or target.db.range > wep_range['max']:
        range_acc -= 0.4

    # Random values for hit calculations
    # hit_roll must be > hit_chance for the player to hit
    chance_hit = random.random()
    hit_roll = random.random()

    # If you're aiming, get a 20% accuracy buff
    if origin.db.isAiming:
        accuracy += 0.2

    # Apply any buffs from your weapon and player
    # bh.check_buffs(weapon, accuracy, 'accuracy')
    # bh.check_buffs(origin, accuracy, 'accuracy')

    # Modify the hit roll by the weapon's accuracy and the range penalty
    # 1.0 is unchanged roll
    # 0.0 is guaranteed miss
    # Higher is better
    hit_roll = hit_roll * accuracy
    return (hit_roll > chance_hit, hit_roll > chance_hit * crit)

def calculate_damage(origin, target, hit, crit):
    '''Calculates damage against a target.'''

    origin.msg('Hit: ' + str(hit))

    if hit is False:
        return 0

    slot = origin.db.held
    weapon = origin.db.weapons[slot]
    damage = weapon.db.damage['base']

    # Roll to find damage based on weapon's min/max
    damage = random.randint(weapon.db.damage['min'], weapon.db.damage['max'])

    origin.msg('Base Damage: ' + str(damage))

    # Apply falloff, if relevant. Falloff is a flat 20% damage penalty
    if weapon.db.damage['falloff'] < target.db.range:
        damage *= 0.8

    # All damage is multiplied by crit
    if crit is True:
        damage = round(damage * weapon.db.crit['mult'])

    origin.msg('Crit Damage: ' + str(damage))

    # Finally, do two stat checks: first against the weapon's bonuses, then against the player's
    damage = bh.check_buffs(weapon, damage, 'damage')
    damage = bh.check_buffs(origin, damage, 'damage')

    origin.msg('Buffed Damage: ' + str(damage))

    # Trigger any perks that function on hit
    ph.trigger_perk(origin, 'hit')

    return damage

def damage_target(damage, target):
    # Actually does the nitty gritty of damaging a target

    msg_post = ''       # Used for our return, which returns any damage-related perk messages

    # Damage the target's health
    target.db.health['current'] -= damage

    # If the target has 0 health, kill it
    if target.db.health['current'] <= 0:
        kill(target)

    return msg_post

def kill(origin):
    # Kills whatever object is called for the function
    if utils.inherits_from(origin, 'typeclasses.npc.NPC'):
        origin.db.state = 'dead'
        for x in find_scripts_by_tag(origin, 'ai'):
            x.restart( interval=origin.db.timer['dead'], start_delay=True )

    return

def revive(origin):
    origin.location.msg_contents( 'Debug: Revival started' )
    
    # Revives the object called for the function
    if hasattr(origin, 'health'):
        origin.db.health['current'] = origin.db.health['max']
        origin.db.shield['current'] = origin.db.shield['max']

def find_scripts_by_tag(obj, tag):
    _list = [ 
        x 
        for x in obj.scripts.all() 
        if tag in x.tags.all() 
    ]

    return _list

def check_time(start, end, duration):
    '''Check to see if duration time has passed between the start and end time.
    Used for checking cooldowns or buff timing.
    
    Always returns false if duration is -1 (for things that last forever).'''

    if duration == -1 or duration == None or start == None or end == None: return False
    if duration < end - start: return True
    else: return False