from typing import TYPE_CHECKING
from dataclasses import dataclass, field
from components.events import EventContext
from typeclasses.objects import Object
from evennia.utils import search, delay

if TYPE_CHECKING:
    from typeclasses.npc import NPC


class BaseBehavior:
    """Base class for behaviors, the AI equivalent of player actions.

    Attrs:
        triggers:   A list of trigger strings; used for "reaction" behaviors
        goal:       A list of goal strings; used for eval"""

    owner: Object = None
    handler: object = None
    triggers: list[str] = []
    goals: list[str] = []

    def __init__(self, owner, handler) -> None:
        self.owner = owner
        self.handler = handler

    def at_queue(self, *args, **kwargs):
        """Hook method for what to do when this behavior is queued. Useful for data storage.
        An example of using this is assigning a target to a queued attack action.

        Args:
            **kwargs:   Context dictionary is passed through this on call"""
        pass

    def at_act(self, *args, **kwargs):
        """Hook method for when the action is called deliberately, such as through queue.

        Args:
            **kwargs:   Context dictionary is passed through this on call"""
        self.owner.location.msg_contents("Debug: Test behavior is acting!")

    def at_react(self, trigger, *args, **kwargs):
        """Hook method for when the action is called via event reaction.

        Args:
            trigger:    The trigger string that caused the react. Useful for layering multiple reactions on one behavior
            **kwargs:   Context dictionary is passed through this on call"""
        pass

    def queue(self):
        """Helper method to add this behavior to the handler's queue."""
        self.handler.enqueue(self)

    def remove(self):
        """Helper method to remove this behavior from the handler's queue."""
        nu_q = [b for b in list(self.handler.queue) if b != self]
        self.handler.queue = nu_q


class BaseBrain:
    """
    The base class for AI brains. Contains an evaluation method and a list of actions
    granted by the brain.

    Attrs:
        handler:    This brain's handler
        granted_behaviors:  The list of behaviors this brain grants
    """

    handler: object
    granted_behaviors: list[BaseBehavior] = []

    def __init__(self, handler) -> None:
        self.handler = handler

    @property
    def behaviors(self) -> list[BaseBehavior]:
        """List of instantiated behaviors (helper method to handler.behaviors)"""
        return self.handler.behaviors

    @property
    def owner(self) -> Object:
        """The object this brain is attached to (helper method to handler.owner)"""
        return self.handler.owner

    def queue(self, behavior: BaseBehavior, **kwargs):
        """Helper method to add a behavior to the handler's queue."""

        # instantiate behavior if necessary, if not related to base then cancel
        instance = behavior
        if not isinstance(behavior, BaseBehavior):
            instance: BaseBehavior = behavior(self.owner, self.handler)

        if not isinstance(instance, BaseBehavior):
            return

        # call the at_queue for the behavior (for instance customization)
        instance.at_queue(**kwargs)

        # queue the instanced action
        self.handler.enqueue(instance)

    def at_think(self, *args, **kwargs):
        """Hook method for thinking; when the AI has nothing in queue, it thinks."""
        pass


class TestBrain(BaseBrain):
    """
    Testing brain
    """

    granted_behaviors: list[BaseBehavior] = [BaseBehavior]

    def at_think(self, *args, **kwargs):
        place = self.owner.location
        place.msg_contents("Debug: test brain is thinking")
        self.queue(BaseBehavior)


class BrainHandler:
    """
    The handler for "brains", AI modules that can be swapped out by builders which grant
    particular behaviors and custom
    """

    ownerref = None
    brain: BaseBrain = None
    queue = None

    def __init__(self, owner, brain: BaseBrain = None, queue=None) -> None:
        self.ownerref = owner.dbref

        # if you don't have a brain hardcoded on init, look for a database or default
        if not brain and self.owner.attributes.has("brain"):
            brain = self.owner.db.brain
        else:
            brain = TestBrain

        # initialize the brain and queue
        self.brain = brain(self)
        self.queue = queue if queue else []

    @property
    def owner(self):
        """The object this handler is attached to."""
        if self.ownerref:
            _owner = search.search_object(self.ownerref)
        if _owner:
            return _owner[0]
        else:
            return None

    @property
    def behaviors(self):
        """A list of instantiated behaviors for use by the handler, combining
        behaviors granted by the database and by the attached brain."""
        behaviorsdb = self.owner.attributes.get("behaviors", default=[])
        behaviorsbrain = self.brain.granted_behaviors if self.brain else []
        uniquebehaviors = list(set(behaviorsdb + behaviorsbrain))
        _return = [behavior(self.owner, self) for behavior in uniquebehaviors]
        return _return

    def act(self, *args, **kwargs):
        """Acts on the next action in the queue. If there is none, thinks."""
        if not self.queue:
            self.brain.at_think(**kwargs)
        else:
            self.queue[0].at_act()
            self.queue[0].remove

        delay(5, self.act)

    def enqueue(self, behavior: BaseBehavior):
        """Queues an behavior"""
        if not self.queue:
            self.queue = []
        self.queue.append(behavior)

    def react(self, trigger, context=None):
        if not context:
            context = {}
        for behavior in self.behaviors:
            behavior: BaseBehavior
            if trigger in behavior.triggers:
                behavior.at_react(trigger, **context)

    def has_behavior():
        pass

    def swap_brain(self, brain: BaseBrain, clear=False):
        """
        Swaps the existing brain for the given brain.

        Args:
            brain:  The brain you want to swap to
        """
        if clear:
            self._clear()

    def reset(self):
        """Resets the AI. This erases all behaviors from its pool, as well as"""

    def change_state(self, state: str):
        pass

    def event_parse(self, event: EventContext):
        self.react(event.eid, event.context)
        pass

    def _clear(self):
        """Clears all db behaviors"""
        self.db.behaviors = []
