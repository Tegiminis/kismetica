import time
from dataclasses import dataclass, asdict, is_dataclass, fields
from typeclasses.objects import Object
from world.rules import make_context
from evennia.utils import search, utils

EVENT = {"source": None, "timestamp": None, "context": None}


@dataclass
class EventContext:
    eid: str
    source: Object
    timestamp: float
    context: dict


class EventManager(object):
    """An event manager handles events, subscribers, and the like."""

    ownerref = None
    _owner = None

    def __init__(self, owner) -> None:
        self.ownerref = owner.dbref
        self.subs = []

    @property
    def owner(self):
        """The object this handler is attached to."""
        if self.ownerref:
            _owner = search.search_object(self.ownerref)
        if _owner:
            return _owner[0]
        else:
            return None

    def subscribe(self, subscriber):
        self.subs.append(subscriber)
        return

    def unsubscribe(self, subscriber):
        if subscriber in self.subs:
            self.subs.remove(subscriber)
        return

    def publish(self, name: str, source, context=None):
        is_dc = is_dataclass(context)

        _c = (
            dict(
                (field.name, getattr(context, field.name)) for field in fields(context)
            )
            if is_dc
            else context
        )
        event: EventContext = EventContext(name, source, time.time(), _c)
        for sub in self.subs:
            sub.event_parse(event)

    def send(self, target, name: str, context: dict = None):
        if hasattr(target, "events"):
            target.events.publish(name, self.owner, context)

    def broadcast(self, name: str, context: dict = None):
        _owner = self.owner
        _contents = _owner.location
        _filtered = [x for x in _contents if hasattr(x, "events")]
        for obj in _filtered:
            self.send(obj, name, context)


def event_parse(event):

    pass
