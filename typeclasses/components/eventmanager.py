import time
from typeclasses.objects import Object

EVENT = {"source": None, "timestamp": None, "context": None}


class EventManager(object):
    """An event manager handles events, subscribers, and the like."""

    owner = None
    subs = []

    def __init__(self, owner) -> None:
        self.owner: Object = owner

    def subscribe(self, subscriber):
        self.subs.append(subscriber)
        pass

    def unsubscribe(self, subscriber):
        if subscriber in self.subs:
            self.subs.remove(subscriber)

    def receive(self, source, name: str, context: dict = None):
        event = {
            "name": name,
            "source": source,
            "timestamp": time.time(),
            "context": context,
        }
        for sub in self.subs:
            sub.event_parse(event)

    def send(self, target, name: str, context: dict = None):
        target.events.receive(self.owner, name, context)

    def broadcast(self, name: str, context: dict = None):
        _owner = self.owner
        _contents = _owner.location
        _filtered = [x for x in _contents if x != self.owner if hasattr(x, "events")]
        for obj in _filtered:
            self.send(obj, name, context)


def event_parse(event):

    pass
