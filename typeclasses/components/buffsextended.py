from evennia.contrib.rpg.buffs.buff import BuffHandler
from typeclasses.components.events import EventContext


class BuffHandlerExtended(BuffHandler):
    def __init__(self, owner=None, dbkey="buffs", autopause=False):
        super().__init__(owner, dbkey, autopause)
        self.sub()

    def sub(self):
        if hasattr(self.owner, "events"):
            self.owner.events.subscribe(self)
        else:
            return

    def event_parse(self, event: EventContext):
        self.trigger(event.eid, event.context)
