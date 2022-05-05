import time

class CooldownHandler(object):
    obj = None 
    
    def __init__(self, obj) -> None:
        self.obj = obj
        if not obj.attributes.has('cooldowns'): self.obj.db.cooldowns = {}

    @property
    def db(self):
        return self.obj.db.cooldowns

    def check(self, key) -> bool:
        ''' True:   Cooldown time is up, cooldown not found
            False:  Cooldown is active'''
        
        # Cooldown not found, therefore you can do whatever you want!
        if key not in self.db.keys(): return True
        
        _cooldown = dict(self.db[key])

        # If cooldown time is up, remove it and return true.      
        if time.time() - _cooldown['start'] > _cooldown['duration']:
            self.remove(key) 
            return True
        
        # Cooldown was found and is still active
        return False
    
    def find(self, key) -> bool: 
        ''' True:   Cooldown is active
            False:  Cooldown time is up, cooldown not found'''
        return not self.check(key)
    
    def start(self, key: str, duration, msg=None):
        '''Sets the initial cooldown time and duration'''
        _cd = {'start': time.time(), 'duration': duration, 'msg': msg}
        self.db[key] = _cd
        _msg = "%s Cooldown: %i seconds" % (key.capitalize(), int(duration))
        self.obj.msg(_msg)

    def extend(self, key, amount):
        '''Extends the current cooldown's duration'''
        self.db[key]['duration'] += amount

    def shorten(self, key, amount):
        '''Shortens the current cooldown's duration'''
        self.db[key]['duration'] -= amount

    def restart(self, key):
        '''Restarts the cooldown by setting start to now. Does not change duration'''
        self.db[key]['start'] = time.time()
    
    def remove(self, key):
        '''Removes a cooldown from the dictionary. Echoes a "finished cooldown" message
        if echo is true.'''
        # Message the object the cooldown is being removed from, if it is puppeted
        if self.db[key]['msg'] is not None:
            if self.obj.has_account: self.obj.msg(self.db[key]['msg'])
            else: self.obj.location.msg(self.db[key]['msg'])
        del self.db[key]
    
    def time_left(self, key) -> float:
        '''Checks to see how much time is left on cooldown with the specified key.'''
        _elapsed = time.time() - self.db[key]['start']
        _dur = self.db[key]['duration']
        return max(0, _dur - _elapsed)