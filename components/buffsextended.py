from evennia.contrib.rpg.buffs.buff import BuffHandler, BaseBuff, Mod
from components.events import GameEvent


class BaseBuffExtended(BaseBuff):
    """
    An extended version of the contrib/rpg/buff buff.

    Changes:
        - Alters `at_trigger` to parse events instead of just a single string
    """

    def at_trigger(self, triggers: list[str], *args, **kwargs):
        pass


class BuffHandlerExtended(BuffHandler):
    """An extended version of the contrib/rpg/buff handler.

    Changes:
        - Implements the `event_parse` method for use by the handler.
        - Automatically subscribes when initialized."""

    def __init__(self, owner=None, dbkey="buffs", autopause=False):
        super().__init__(owner, dbkey, autopause)
        self.sub()

    def sub(self):
        if hasattr(self.owner, "events"):
            self.owner.events.subscribe(self)
        else:
            return

    def event_parse(self, event: GameEvent):
        self.event_trigger(event)

    def super_get(
        self,
        tag: str = None,
        bufftype: BaseBuff = None,
        stat: str = None,
        triggers: list[str] = None,
        source=None,
        cachekey: str = None,
        cachevalue=None,
        to_filter=None,
    ):
        """
        A combined version of all getters except the base get and get_all.

        Args:
            tag:        The string to search for
            bufftype:   The buff class to search for
            stat:       The string identifier to find relevant mods
            trigger:    The string identifier to find relevant buffs
            source:     The source you want to filter buffs by
            cachekey:   The key of the cache value to check
            cachevalue: The value to match to. If None, merely checks to see if the value exists
            to_filter:  A dictionary you wish to slice. If not provided, uses the whole buffcache.

        Returns a dictionary sliced according to the arguments you provide. Only buffs matching all
        arguments will be returned.
        """
        # either an empty dict, all buffs, or the dictionary to filter
        buffs = self.get_all() if not to_filter else dict(to_filter)
        if not buffs:
            return

        # slicing the dictionary
        if tag:
            buffs = {k: buff for k, buff in buffs.items() if tag in buff.tags}
        if bufftype:
            buffs = {k: buff for k, buff in buffs.items() if isinstance(buff, BaseBuff)}
        if stat:
            buffs = {
                k: buff
                for k, buff in buffs.items()
                for m in buff.mods
                if m.stat == stat
            }
        if triggers:
            _t = set(triggers)
            buffs = {
                k: buff for k, buff in buffs.items() if bool(_t & set(buff.triggers))
            }
        if source:
            buffs = {k: buff for k, buff in buffs.items() if buff.source == source}
        if cachekey:
            ck, cv = cachekey, cachevalue
            if not cv:
                buffs = {
                    k: buff for k, buff in buffs.items() if ck in buff.cache.keys()
                }
            else:
                buffs = {
                    k: buff
                    for k, buff in buffs.items()
                    if buff.cache.get(ck, None) == cv
                }

        # return our sliced dictionary (or none, if nothing was found)
        return buffs

    def event_trigger(self, event: GameEvent, to_trigger=None):
        """Calls the at_trigger method on all buffs with the matching trigger.

        Args:
            trigger:    The string identifier to find relevant buffs. Passed to the at_trigger method.
            context:    (optional) A dictionary you wish to pass to the at_trigger method as kwargs
            to_trigger: (optional) Dictionary of instanced buffs to use instead of a new default dictionary
        """
        triggers = event.tags
        _effects = self.super_get(triggers=triggers, to_filter=to_trigger)
        context = dict(event.context)
        if not _effects:
            return
        if not context:
            context = {}

        # filter out any buffs whose conditional fails or which are paused
        _to_trigger = {
            k: buff
            for k, buff in _effects.items()
            if buff.conditional(**context)
            if not buff.paused
        }

        # trigger all buffs whose trigger matches the trigger string
        for buff in _to_trigger.values():
            buff: BaseBuffExtended
            buff.at_trigger(triggers, **context)
