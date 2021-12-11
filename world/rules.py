import random
import time
from typeclasses.context import DamageContext, generate_context
from evennia import DefaultCharacter, utils
import typeclasses.handlers.buffhandler as bh
from typeclasses.weapon import Weapon

slot = {'kinetic':0 , 'energy':1 , 'power':2}
element = {'neutral':0 , 'void':1 , 'solar':2, 'arc':3}
ammo = {'primary':0 , 'special':1 , 'power':2}
armor = {'head':0 , 'arms':1 , 'chest':2, 'legs':3, 'class':4}

def basic_attack(attacker: DefaultCharacter, defender: DefaultCharacter):
    '''The most basic attack a player can perform. Uses a weapon, held by origin, to attack the target.
    
    Attacker must have a weapon in db.held, otherwise this command will return an error.
    '''
    weapon: Weapon = attacker.db.held
    now = time.time()

    if utils.inherits_from(defender, 'typeclasses.npc.NPC') or defender.db.crucible == True:
        # The string of "hits" used for messaging. Looks like this once everything's done: "15! 10! Miss! 10! 10!"
        d_msg = ''

        # Hit calculation and initial attack messages
        hit = roll_hit(attacker, defender)
        attacker.msg( "\n|n" + (weapon.db.msg['attack'] % ('you',defender.named)).capitalize())
        if hit[1]: d_msg += '|yCrit! '

        # Damage calculation and messaging
        damage = calculate_damage(attacker, defender, *hit)    
        d_msg += "%i damage!" % damage
        dc : DamageContext = generate_context(attacker, defender, damage, weapon)             

        if hit[0]:
            damage_target(damage, defender)
            attacker.msg( d_msg )

            bh.trigger_effects(weapon, defender, 'hit', dc)
            bh.trigger_effects(attacker, defender, 'hit', dc)
            
            if hit[1]:
                bh.trigger_effects(weapon, defender, 'crit', dc)
                bh.trigger_effects(attacker, defender, 'crit', dc)
            
            bh.trigger_effects(defender, attacker, 'thorns', dc)
            bh.trigger_effects(defender, defender, 'injury', dc)
        else:
            attacker.msg( weapon.db.msg['miss'] )

        attacker.db.cooldown = now

        utils.delay(weapon.rpm, attacker.msg, weapon.db.msg['cooldown'])

def roll_hit(attacker, defender):
    '''
    Rolls to hit a defender. This function requires the attacker to have a weapon.
    
    Args:
        attacker: The attacker.
        defender: The defender.

    Returns a tuple of bools: was hit, and was crit
    '''
    # Get the weapon used, required for a good portion of the hit calculation
    weapon: Weapon = attacker.db.held

    # Apply all accuracy and crit buffs for attack, and evasion buffs for defense
    accuracy = weapon.accuracy
    accuracy = bh.check_stat_mods(attacker, accuracy, 'accuracy')
    crit = weapon.critChance
    crit = bh.check_stat_mods(attacker, crit, 'crit')
    evasion = defender.evasion
    evasion = bh.check_stat_mods(defender, evasion, 'evasion')

    # Apply a range penalty equal to 20% times the difference in defender and attacker range
    range_penalty = 1.0
    if defender.db.range < weapon.cqc: range_penalty -= 0.2 * abs(weapon.cqc - defender.db.range)

    # Random values for hit calculations
    # hit must be > evasion for the player to hit
    hit = random.random()
    dodge = random.random()

    # Modify the hit roll by the accuracy value.
    hit = hit * accuracy
    dodge = dodge * evasion

    return (hit > dodge, hit > dodge * crit)

def calculate_damage(attacker, defender, hit, crit) -> float:
    '''Calculates damage against a defender.'''

    if hit is False:
        return 0.0

    weapon: Weapon = attacker.db.held

    # Roll to find damage based on weapon's min/max, and apply weapon buffs
    # attacker.msg('Debug Base Damage: ' + str(weapon.db.damage))
    damage = weapon.damage

    # Apply falloff, if relevant. Falloff is a flat 20% damage penalty
    if weapon.falloff < defender.db.range: damage *= 0.8

    # All damage is multiplied by crit
    if crit is True: 
        damage = round(damage * weapon.critMult)

    # attacker.msg('Crit Damage: ' + str(damage))

    # Apply all attacker buffs to damage
    damage = bh.check_stat_mods(attacker, damage, 'damage')
    # attacker.msg('Debug Attacker-modified Damage: ' + str(damage))

    # Apply all defender buffs to damage
    damage = bh.check_stat_mods(defender, damage, 'injury')
    # attacker.msg('Debug Defender-modified Damage: ' + str(damage))

    bh.cleanup_buffs(attacker)
    return round(damage)

def damage_target(damage, target):

    # Damage the target's health
    target.db.health -= damage

    # If the target has 0 health, kill it
    if target.db.health <= 0:
        kill(target)

    return

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
        origin.db.health = origin.db.health['max']

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