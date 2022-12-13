from evennia.contrib.rpg.buffs.buff import BuffHandler


class BuffHandlerExtended(BuffHandler):
    def __init__(self, owner, dbkey=..., autopause=...):
        super().__init__(owner, dbkey, autopause)
        if hasattr(owner, "events"):
            owner.events.subscribe(self)

    def event_parse(self, event):
        _event = dict(event)
        self.trigger(event["name"], event["context"])
