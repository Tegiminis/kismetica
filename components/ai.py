from typing import TYPE_CHECKING
from dataclasses import dataclass, field
from typeclasses.npc import NPC
from evennia.utils import search

if TYPE_CHECKING:
    from typeclasses.npc import NPC


@dataclass
class BaseBehavior:
    """Base class for behaviors, the AI equivalent of player actions.

    Attrs:
        triggers:   A list of trigger strings; used for "reaction" behaviors"""

    triggers: list[str] = field(default_factory=list)

    def at_act(self, *args, **kwargs):
        """Hook method for when the action is called via queue or brain eval.

        Args:
            **kwargs:   Context dictionary is passed through this on call"""
        pass

    def at_react(self, trigger, *args, **kwargs):
        """Hook method for when the action is called via event reaction
        Args:
            trigger:    The trigger string that caused the react. Useful for layering multiple reactions on one behavior
            **kwargs:   Context dictionary is passed through this on call"""
        pass


@dataclass
class BaseBrain:
    """The base class for AI brains.

    Components:
        behaviors:  The list of behaviors this brain grants
        overwrite:"""

    behaviors: list[BaseBehavior] = field(default_factory=list)
    clear: bool = False

    def eval(self, *args, **kwargs):
        pass

    pass


class BrainHandler:

    ownerref = None
    brain: BaseBrain = None

    def __init__(self, owner, brain=None) -> None:
        self.ownerref = owner.dbref

        # initialize brain, either from init or database
        if brain:
            self.brain = brain
        elif self.owner.attributes.has("brain"):
            self.brain = self.owner.db.brain
        else:
            pass

        # initialize behavior list
        blist = list(self.behaviors).extend(self.brain.behaviors)

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
        return self.owner.db.behaviors

    def act(self, behavior: BaseBehavior):
        """Performs a behavior"""

    def enqueue(self, behavior: BaseBehavior):
        """Queues an behavior"""

    def react(self, trigger, context=None):
        if not context:
            context = {}
        for behavior in self.behaviors:
            instance: BaseBehavior = behavior()
            if trigger in instance.triggers:
                instance.at_react(trigger, **context)

    def has_behavior():
        pass

    def swap_brain():
        pass

    def change_state(self, state: str):
        pass

    def event_parse(self):
        pass
