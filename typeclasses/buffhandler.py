from .objects import Object
import time

def stat_check(obj: Object, base, stat: str):    

    # Buff handler assignment, so we can find the relevant buffs
    bh = obj.db.buffhandler

    # Do the first bit of buff cleanup
    # buff_cleanup(bh)

    # Add all arithmetic buffs together
    add_dict = find_buffs_by_value(bh, 'eff', 'add')
    add = calc_buff(add_dict)

    # Add all multiplication buffs together
    mult_dict = find_buffs_by_value(bh, 'eff', 'mult')
    mult = calc_buff(mult_dict)

    # The final result
    final = (base + add) * (1 + mult)

    return final

# Find all buffs in the buffhandler dictionary according to a specific value (typically stat or effect)
def find_buffs_by_value(bh, key: str, val) -> dict:
    dict = { k:v for k,v in bh.items() if v.get(key) == val }
    return dict

# Given a dictionary of buffs, add all their values together
def calc_buff(buffs: dict):
    x = 0.0
    for k,v in buffs.items():
        b = v.get('base')
        s = v.get('stacks')
        ps = v.get('perstack')

        x += b + ((1 - s) * ps)
    return x

# Checks all buffs on the handler and cleans up old ones
def buff_cleanup(handler):
    for k,v in handler.items():
        now = time.time()
        dur = v.get('duration')
        t = v.get('time')
        if dur == -1:
            break
        if dur > now - t:
            handler.pop(k)