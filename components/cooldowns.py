from dataclasses import dataclass
import time
from evennia import utils

from evennia.utils import search


@dataclass
class Cooldown:
    """Dataclass for cooldowns"""

    key: str
    start: float
    duration: int | float
    message: str
    context: dict

    @property
    def timeleft(self):
        """Returns time left in the cooldown"""
        return max(0, self.duration - (time.time() - self.start))

    @property
    def ready(self):
        """Boolean for if this cooldown is ready"""
        return time.time() - self.start > self.duration


class CooldownHandler(object):
    """
    Cooldowns are simple timestamps and strings used for quick-and-easy timers.
    They save to the database and can be manipulated by various handler methods.

    """

    ownerref = None
    dbkey = "cooldowns"
    autopause = False

    def __init__(self, owner, dbkey=dbkey, autopause=autopause):
        self.ownerref = owner.dbref
        self.dbkey = dbkey
        self.autopause = autopause

    @property
    def owner(self):
        """The object this handler is attached to"""
        return search.search_object(self.ownerref)[0]

    @property
    def db(self):
        """The object attribute we use for the cooldown database. Auto-creates if not present.
        Convenience shortcut (equal to `self.owner.db.dbkey`)"""
        if not self.owner.attributes.has(self.dbkey):
            self.owner.attributes.add(self.dbkey, {})
        return self.owner.attributes.get(self.dbkey)

    def get(self, key) -> Cooldown:
        """
        Gets a cooldown.

        Args:
            key:    The cooldown key to look up

        Returns either None (if expired or absent) or a cooldown dataclass for access.
        You should do truthy checks with this function.
        """
        if key in self.db:
            cd_cache = dict(self.db[key])
            cooldown = Cooldown(key=key, **cd_cache)

            # ready check (delete cooldown if ready)
            if cooldown.ready:
                self.remove(key)
                del cooldown
                return None

            # return cooldown if still active + exists
            return cooldown

        return None

    def add(
        self, key: str, duration=1, added=None, finished=None, stifle=False, **kwargs
    ):
        """
        Adds a cooldown to the handler. This is saved as a dictionary on the object's db.

        Args:
            key:        The key string the cooldown goes by (for example, "attack")
            duration:   The duration in seconds
            added:      The message to display when the cooldown is added (default: Key:Seconds)
            finished:   The message you wish to display when the cooldown expires
            echo:       (default: `False`) If `True`, sends the cooldown message to the attached object.
        """
        # dictionary creation and application
        cooldown = {
            "start": time.time(),
            "duration": duration,
            "message": finished,
            "context": {},
        }
        self.db[key] = cooldown

        # cooldown messaging
        if not stifle:
            DEFAULT_MESSAGE = "{key} Cooldown: {duration} seconds"
            message = added if added else DEFAULT_MESSAGE
            formatted = message.format(key=key, **cooldown).capitalize()
            self.owner.msg(formatted)

        utils.delay(duration, self.cleanup)

    def extend(self, key, amount):
        """Extends an existing cooldown's duration"""
        self.db[key]["duration"] += amount

    def shorten(self, key, amount):
        """Shortens an existing cooldown's duration"""
        self.db[key]["duration"] -= amount

    def restart(self, key):
        """Restarts the cooldown by setting start to now. Does not change duration"""
        self.db[key]["start"] = time.time()

    def remove(self, key):
        """
        Removes a cooldown from the dictionary.

        Args:
            key:    The key string of the cooldown to remove
            echo:   (default: `False`) If `True`, sends the cooldown message to the attached object.
        """
        # Message the object the cooldown is being removed from, if it is puppeted
        cooldown = Cooldown(key, **self.db[key])
        if cooldown.message:
            if self.owner.has_account:
                self.owner.msg(cooldown.message)
            else:
                self.owner.location.msg(cooldown.message)
        del self.db[key]

    def time_left(self, key) -> float:
        """Checks to see how much time is left on cooldown with the specified key."""
        cooldown = self.get(key)
        if cooldown:
            return cooldown.timeleft
        return 0

    def cleanup(self):
        """Does a quick cleanup of cooldowns to ensure they are still valid/active, removing any that aren't"""
        for key in self.db:
            instance = self.get(key)
            del instance
