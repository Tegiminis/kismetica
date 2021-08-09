from typeclasses.context import generate_context
from typeclasses.buff import Buff
import random
from random import randint
from typeclasses import characters as Character
from evennia import utils
from typeclasses.objects import Object
import time
import typeclasses.handlers.buffhandler as bh
import typeclasses.handlers.perkhandler as ph

slot = {'kinetic':0 , 'energy':1 , 'power':2}
element = {'neutral':0 , 'void':1 , 'solar':2, 'arc':3}
ammo = {'primary':0 , 'special':1 , 'power':2}
armor = {'head':0 , 'arms':1 , 'chest':2, 'legs':3, 'class':4}

def attack(attacker, defender):
    '''Attacks the defender. Used by the "attack" command and NPC attacks. Attacker must have a weapon in db.held, otherwise this command will return an error.'''

    pass

def roll_hit(attacker, defender):
    '''
    Rolls to hit a defender. This function requires the attacker to have a ranged weapon.
    
    Args:
        attacker: The attacker.
        defender: The defender.

    Returns a tuple of bools: was hit, and was crit
    '''
    # Get the weapon used, required for a good portion of the hit calculation
    weapon = attacker.db.held
    accuracy = weapon.db.damage['acc']
    crit = weapon.db.crit['chance']

    # Range is simple
    # Check the weapon's range, and the enemy's range
    # If the weapon's range aligns with the enemy's range, there's no penalty
    # If the range exceeds min/max, suffer an accuracy penalty (currently, 40% penalty)
    wep_range = weapon.db.range
    range_acc = 1.0
    if defender.db.range < wep_range['min'] or defender.db.range > wep_range['max']:
        range_acc -= 0.4

    # Random values for hit calculations
    # hit_roll must be > hit_chance for the player to hit
    chance_hit = random.random()
    hit_roll = random.random()

    # If you're aiming, get a 20% accuracy buff
    if attacker.db.isAiming:
        accuracy += 0.2

    # Apply any buffs from your weapon and player
    # accuracy = check_stat_mods(weapon, accuracy, 'accuracy')
    # accuracy = check_stat_mods(attacker, accuracy, 'accuracy')

    # Modify the hit roll by the weapon's accuracy and the range penalty
    # 1.0 is unchanged roll
    # 0.0 is guaranteed miss
    # Higher is better
    hit_roll = hit_roll * accuracy
    return (hit_roll > chance_hit, hit_roll > chance_hit * crit)

def calculate_damage(attacker, defender, hit, crit) -> float:
    '''Calculates damage against a defender.'''

    if hit is False:
        return 0.0

    weapon = attacker.db.held
    damage = weapon.db.damage['base']

    # Roll to find damage based on weapon's min/max
    damage = random.randint(weapon.db.damage['min'], weapon.db.damage['max'])

    # attacker.msg('Base Damage: ' + str(damage))

    # Apply falloff, if relevant. Falloff is a flat 20% damage penalty
    if weapon.db.damage['falloff'] < defender.db.range:
        damage *= 0.8

    # All damage is multiplied by crit
    if crit is True:
        damage = round(damage * weapon.db.crit['mult'])

    # attacker.msg('Crit Damage: ' + str(damage))

    # Finally, do two stat checks: first against the weapon's bonuses, then against the player's
    weapon_buffed = check_stat_mods(weapon, damage, 'damage')
    damage = weapon_buffed

    attacker_buffed = check_stat_mods(attacker, damage, 'damage')
    damage = attacker_buffed
    
    # Trigger any perks that function on hit. Returns a list of the perk's messages.
    # msg = ph.trigger_effects(weapon, 'hit')
    # msg += ph.trigger_effects(attacker, 'hit')

    # attacker.msg(msg)

    bh.cleanup_buffs(attacker)
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

def check_stat_mods(obj: Object, base: float, stat: str):    
    '''Finds all buffs and traits related to a stat and applies their effects.
    
    Args:
        obj: The object with a buffhandler
        base: The base value you intend to modify
        stat: The string that designates which stat buffs you want
        
    Returns the base value modified by the relevant buffs, and any messaging.'''

    # Buff cleanup to make sure all buffs are valid before processing
    bh.cleanup_buffs(obj)

    # Buff handler assignment, so we can find the relevant buffs
    buffs = []
    traits = []
    if not obj.db.buffs and not obj.db.traits: return base
    else: 
        buffs = obj.db.buffs.values()
        traits = obj.db.traits.values()

    # Find all buffs and traits related to the specified stat.
    buff_list: list = bh.find_mods_by_value(buffs, 'stat', stat)
    trait_list: list = bh.find_mods_by_value(traits, 'stat', stat)
    stat_list = buff_list + trait_list

    if not stat_list: return base

    # Add all arithmetic buffs together
    add_list = bh.find_mods_by_value(stat_list, 'modifier', 'add')
    add = bh.calculate_mods(add_list, "add")

    # Add all multiplication buffs together
    mult_list = bh.find_mods_by_value(stat_list, 'modifier', 'mult')
    mult = bh.calculate_mods(mult_list, "mult")

    # The final result
    final = (base + add) * (1 + mult)

    # Run the "after check" functions on all relevant buffs
    for x in stat_list:
        buff: Buff = x.get('ref')()
        context = generate_context(obj, obj, buff=buff.id, handler=obj.db.buffs)
        buff.after_check(context)

    return final