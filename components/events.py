import time
from dataclasses import dataclass, asdict, is_dataclass, fields, field
from typeclasses.objects import Object
from components.context import asdict_shallow
from evennia.utils import search, utils

EVENT = {"source": None, "timestamp": None, "context": None}


@dataclass
class EventContext:
    eid: str
    source: Object
    timestamp: float
    context: dict
    tags: list[str] = field(default_factory=list)


class EventHandler(object):
    """An event manager handles events, subscribers, and the like.

    This handler must be initialized like so:

    ```python
    @lazy_property
    def events(self) -> EventHandler:
        return EventHandler(self)
    ```

    Otherwise it will function improperly.
    """

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

    def queue(self, source, context, tags):
        pass

    def subscribe(self, subscriber):
        """Subscribes to this event manager. Subscribing objects must implement
        the "event_parse" method for publishing to be successful.

        Args:
            subscriber: The subscribing object to add

        All subscribers are cleared on server reload/init."""
        self.subs.append(subscriber)
        return

    def unsubscribe(self, subscriber):
        """Removes a specific subscriber. Used, for example, by equippable objects
        whose events are shared with their character.

        Args:
            subscriber: The subscribing object to remove

        Note that a server reload will wipe all subs from this manager."""
        if subscriber in self.subs:
            self.subs.remove(subscriber)
        return

    def publish(self, name: str, source, context=None, tags=[]):
        """Publish an event to this handler's subscribers.

        Args:
            name:   The event string, used for triggering stuff
            source:     The source object of the event
            context:    The dataclass or dictionary holding our event's context"""
        # validate and dict-ify the context
        context = {} if not context else context
        is_dc = is_dataclass(context)
        _c = asdict_shallow(context) if is_dc else context

        # create event context
        event: EventContext = EventContext(name, source, time.time(), _c, tags)

        # event parsing
        for sub in self.subs:
            # any objects subscribing to an event manager should implement this method
            sub.event_parse(event)

    def send(self, targets, name: str, context: dict = None):
        """Sends an event to another object (or multiple) for publishing to its subscribers.
        This counts as originating from the object this handler is assigned to.

        Args:
            targets: The list of targets. Requires an EventHandler assigned to "events" property
            name:   The event string, used for triggering stuff
            context:    The dataclass or dictionary holding our event's context."""
        if not isinstance(targets, list):
            targets = [targets]
        aware_targets = [obj for obj in targets if hasattr(obj, "events")]
        for target in aware_targets:
            target.events.publish(name, self.owner, context)

    def broadcast(self, name: str, context: dict = None, include=False):
        """Broadcasts an event to all objects in the same location.

        Args:
            name:   The event string, used for triggering stuff
            context:    The dataclass or dictionary holding our event's context.
            include:    (default: False) Include the broadcaster in the broadcast."""
        _owner = self.owner
        loc = _owner.location
        eventaware = [x for x in loc if hasattr(x, "events")]
        for obj in eventaware:
            self.send(obj, name, context)


def event_parse(event):
    pass
