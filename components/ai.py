from typing import TYPE_CHECKING
from dataclasses import dataclass, field
from components.events import GameEvent
from world.rules import capitalize
from typeclasses.objects import Object
from evennia.utils import search, delay
import random
from collections import deque

if TYPE_CHECKING:
    from typeclasses.npc import NPC
    from components.cooldowns import Cooldown

DEFAULT_THINK_MESSAGE = "{owner} looks lost in thought."
DEFAULT_PATROL_MESSAGE = "{owner} considers where to go next."
DEFAULT_TARGET_MESSAGE = "{owner} sets their sights on {target}."
DEFAULT_STALK_MESSAGE = "{owner} tracks {target} to an adjacent room."
DEFAULT_DEAD_MESSAGE = "{owner} stews silently in non-existence."


class BaseBehavior:
    """
    Base class for behaviors, the AI equivalent of player actions.

    Attrs:
        triggers:   A list of trigger strings; used for "reaction" behaviors
        goal:       A list of goal strings; used for eval
        cooldown:    The cooldown string to check for and use; if not ready, behavior doesn't fire
        delay:       The actual cooldown delay
    """

    owner: Object = None
    handler: object = None
    brain: object = None
    triggers: list[str] = []
    goals: list[str] = []
    cooldown: str = "global"
    delay: int = 5

    def __init__(self, owner, handler) -> None:
        self.owner = owner
        self.handler = handler
        self.brain = self.handler.brain

    def at_init(self, *args, **kwargs):
        """Hook method run after mandatory init"""
        pass

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
        pass

    def at_react(self, trigger, *args, **kwargs):
        """Hook method for when the action is called via event reaction.

        Args:
            trigger:    The trigger string that caused the react. Useful for layering multiple reactions on one behavior
            **kwargs:   Context dictionary is passed through this on call"""
        pass

    def queue(self, *args, **kwargs):
        """Helper method to add this behavior to the handler's queue."""
        self.handler.enqueue(self, **kwargs)

    def remove(self, *args, **kwargs):
        """Helper method to remove this behavior from the handler's queue."""
        nu_q = [b for b in list(self.handler.queue) if b != self]
        self.handler.queue = nu_q


class TestBehavior(BaseBehavior):
    def at_act(self, *args, **kwargs):
        place = self.owner.location
        message = "{0} realized they have no brain, and so cannot think!"
        formatted = capitalize(message.format(self.owner))
        place.msg_contents(formatted)
        return super().at_act(*args, **kwargs)


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

    def __init__(self, handler=None) -> None:
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
        """
        Helper method to add a behavior to the handler's queue. Passes kwargs to queue hook on behavior

        Args:
            behavior:   The behavior to add to the queue
        """

        # instantiate behavior if necessary, if not related to base then cancel
        instance = behavior
        if not isinstance(behavior, BaseBehavior):
            instance: BaseBehavior = behavior(self.owner, self.handler)

        if not isinstance(instance, BaseBehavior):
            return

        # queue the instanced action
        self.handler.enqueue(instance, **kwargs)

    def pre_think(self, *args, **kwargs):
        """Hook method run before thinking; always run, whether brain thinks or acts"""

    def at_think(self, *args, **kwargs):
        """Hook method for thinking; when the AI has nothing in queue, it thinks."""
        pass

    def scan(self, target=None, location=None):
        """
        Find all potential targets.

        Args:
            target:     (optional) The target you wish to search for; all potential targets by default
            location:   (optional) The location you wish to search; current location by default

        Returns a list containing one of three sets:
            target:     If the target is specified and in location
            targets:    If target is unspecified but potential targets are in location
            empty:      If target is specified and unfound, or no targets are found
        """
        to_return = {}
        place = location if location else self.owner.location

        # get list of targets and target to find
        targets = {
            obj
            for obj in place.contents_get(exclude=self.owner)
            if obj.has_account and not obj.is_superuser
        }
        target = set([target]) if target else set([])

        # find target via set intersection
        to_return = targets.intersection(target)
        if not to_return and targets:
            to_return = targets

        return list(to_return)

    def find_exits(self):
        """
        Find all valid exits to the current location.
        """
        here = self.owner.location
        exits = [exi for exi in here.exits if exi.access(self, "traverse")]
        return exits

    def search(self, target=None):
        """
        Searches nearby rooms for specified target.

        Args:
            target: (optional) The target to search for. If none, returns destination of first target found
        """
        dest = None
        exits = self.find_exits()

        if exits:
            dest = next((exi for exi in exits if self.scan(target, exi)), None)
        return dest

    def patrol(self):
        """
        Scan the current room for exits, and randomly pick one.
        """
        # target found, look for an exit.
        exits = self.find_exits()
        destination = None
        if exits:
            if len(exits) == 1:
                destination = exits[0].destination
            else:
                destination = random.choice(exits).destination
        else:
            # no exits! teleport to home to get away.
            destination = self.home

        return destination


class TestBrain(BaseBrain):
    """
    Testing brain
    """

    granted_behaviors: list[BaseBehavior] = [TestBehavior]

    def at_think(self, *args, **kwargs):
        self.queue(TestBehavior)


class BehaviorAttack(BaseBehavior):
    target = None

    def at_queue(self, target=None, *args, **kwargs):
        self.target = target

    def at_act(self, *args, **kwargs):
        owner = self.owner
        targets = self.brain.scan(self.target)
        if self.target in targets:
            owner.npc_attack(self.target, **kwargs)
            self.queue(**{"target": self.target})
        else:
            self.handler.think(**kwargs)


class BehaviorMove(BaseBehavior):
    destination = None
    delay = 3

    def at_queue(self, destination=None, *args, **kwargs):
        self.destination = destination

    def at_act(self, *args, **kwargs):
        self.owner.move_to(self.destination)


class PatrolBrain(BaseBrain):
    """Brain for patrolling enemies"""

    target = None

    def at_think(self, *args, **kwargs):
        owner = self.owner
        place = self.owner.location
        messaging: dict = self.owner.attributes.get("messaging", {})

        if not self.owner.tags.has("dead", "combat"):
            message = messaging.get("think", DEFAULT_THINK_MESSAGE)
            destination = None

            found = self.scan(self.target)

            # did not find any targets in current room
            if not found:
                destination = self.search(self.target)
                # found either existing or new targets in nearby room, stalk
                if destination:
                    self.target = self.scan(self.target, destination)[0]
                    message = messaging.get("stalk", DEFAULT_STALK_MESSAGE)
                    self.target.msg("You feel eyes on your back...")
                    self.queue(BehaviorMove, **{"destination": destination})
                # no target found, patrol
                else:
                    self.target = None
                    destination = self.patrol()
                    message = messaging.get("patrol", DEFAULT_PATROL_MESSAGE)
                    self.queue(BehaviorMove, **{"destination": destination})
            # found targets in current room, either current or new targets
            elif found:
                self.target = found[0]
                message = messaging.get("target", DEFAULT_TARGET_MESSAGE)
                self.queue(BehaviorAttack, **{"target": self.target})
        else:
            message = messaging.get("dead", DEFAULT_DEAD_MESSAGE)

        # send ye message
        mapping = {"owner": self.owner, "target": self.target}
        formatted = capitalize(message.format(**mapping))
        place.msg_contents(formatted)

    def scan(self, target=None, location=None):
        """
        Find all potential targets.

        Args:
            target:     (optional) The target you wish to search for; all potential targets by default
            location:   (optional) The location you wish to search; current location by default

        Returns a list containing one of three sets:
            target:     If the target is specified and in location
            targets:    If target is unspecified but potential targets are in location
            empty:      If target is specified and unfound, or no targets are found
        """
        to_return = {}
        place = location if location else self.owner.location

        # get list of targets and target to find
        targets = {
            obj
            for obj in place.contents_get(exclude=self.owner)
            if obj.has_account
            if not obj.is_superuser
            if not obj.tags.has("dead", category="combat")
        }
        target = set([target]) if target else set([])

        # find target via set intersection
        to_return = targets.intersection(target)
        if not to_return and targets:
            to_return = targets

        return list(to_return)

    def find_exits(self):
        """
        Find all valid exits to the current location.
        """
        here = self.owner.location
        exits = [exi for exi in here.exits if exi.access(self, "traverse")]
        return exits

    def search(self, target=None):
        """
        Searches nearby rooms for specified target.

        Args:
            target: (optional) The target to search for. If none, returns destination of first target found
        """
        dest = None
        exits = self.find_exits()

        for exi in exits:
            targets = self.scan(target, exi.destination)
            if targets:
                self.target = targets[0]
                dest = exi.destination
                break
        return dest

    def patrol(self):
        """
        Scan the current room for exits, and randomly pick one.
        """
        # target found, look for an exit.
        exits = self.find_exits()
        destination = None
        if exits:
            if len(exits) == 1:
                destination = exits[0].destination
            else:
                destination = random.choice(exits).destination
        else:
            # no exits! teleport to home to get away.
            destination = self.home

        return destination


class BrainHandler:
    """
    The handler for "brains", AI modules that can be swapped out by builders which grant
    particular behaviors and custom
    """

    ownerref = None
    brain: BaseBrain = None
    queue: deque = None

    def __init__(self, owner) -> None:
        self.ownerref = owner.dbref
        self.queue = deque([])
        # start thinking
        self.act()

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

    def act(self, idle=5, *args, **kwargs):
        """
        Acts on the next action in the queue. If there is none, thinks.

        Args:
            idle:   (default: 5) The number of seconds to wait after thinking before thinking again
        """
        # oops check
        brain = self.owner.attributes.get("brain", TestBrain)

        # initialize the brain and queue
        if not isinstance(brain, BaseBrain):
            brain = brain(self)

        place = self.owner.location
        thinking: Cooldown = self.owner.cooldowns.get("think")
        if thinking:
            return

        if not brain.handler:
            brain.handler = self

        self.brain = brain

        # think if the queue is empty, otherwise get frontmost behavior instance
        brain.pre_think(**kwargs)
        instance: BaseBehavior = None
        _delay = idle
        messaging: dict = self.owner.attributes.get("messaging", {})

        if not self.queue:
            self.think(**kwargs)
            self.owner.cooldowns.add("think", idle)
        elif not self.owner.tags.has("dead", "combat"):
            # behavior instance
            instance: BaseBehavior = self.queue[0]

            # check cooldown and if not ready delay until you are ready
            cooldown: Cooldown = self.owner.cooldowns.get(instance.cooldown)
            _delay = cooldown.timeleft if cooldown else idle

            # if ready, do the action and remove the instance
            if not cooldown:
                self.owner.cooldowns.add(instance.cooldown, instance.delay)
                _delay = instance.delay
                instance.at_act(**kwargs)
                self.queue.popleft()

        # keep this thread going
        delay(_delay, act_thread, self.owner)

    def think(self, *args, **kwargs):
        """No act, only think"""
        self.brain.at_think(**kwargs)

    def enqueue(self, behavior: BaseBehavior, **kwargs):
        """Queues an behavior at the end"""
        if not self.queue:
            self.queue = deque([])

        instance = (
            behavior
            if isinstance(behavior, BaseBehavior)
            else behavior(self.owner, self)
        )
        instance.at_queue(**kwargs)
        self.queue.append(behavior)

    def interrupt(self, behavior: BaseBehavior, **kwargs):
        """Adds a behavior to the front of the queue (next in line)"""
        if not self.queue:
            self.queue = deque([])

        instance = (
            behavior
            if isinstance(behavior, BaseBehavior)
            else behavior(self.owner, self)
        )
        instance.at_queue(**kwargs)
        self.queue.appendleft(behavior)

    def react(self, trigger, context=None):
        """Triggers the reaction behaviors with the specified trigger."""
        if not context:
            context = {}
        for behavior in self.behaviors:
            behavior: BaseBehavior
            if trigger in behavior.triggers:
                behavior.at_react(trigger, **context)

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

    def event_parse(self, event: GameEvent):
        self.react(event.eid, event.context)

    def _clear(self):
        """Clears all db behaviors"""
        self.db.behaviors = []


def act_thread(owner):
    """Maintains the act thread by being pickleable"""
    owner.ai.act()
