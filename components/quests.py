from components.buffsextended import BuffHandlerExtended, BaseBuff
from components.events import EventContext


class BaseQuest(BaseBuff):
    """
    A quest class. Uses the buff class as a base, causing it to trigger off the same events.

    Methods:
        at_progressed:
    """

    goals: dict = None
    xp = 10

    @property
    def triggers(self):
        return self.goals.keys()

    def at_apply(self, *args, **kwargs):
        progress = {goal: 0 for goal in self.goals}
        self.update_cache({"progress": progress})

    def at_trigger(self, trigger: str, *args, **kwargs):
        """
        Hook method for when a quest's progress advances. Defaults to 1 point of progress per event.
        """
        progress = dict(self.progress)
        if trigger in self.triggers:
            progress[trigger] += 1

        completed = [progress[goal] >= self.goals[goal] for goal in self.triggers]
        print(progress)
        print(self.goals)
        print(completed)
        if all(completed):
            self.at_complete(*args, **kwargs)
        else:
            self.progress = {
                goal: min(progress[goal], self.goals[goal]) for goal in self.triggers
            }

    def at_complete(self, *args, **kwargs):
        """Hook method for when this quest completes."""
        self.owner.gain_xp(1000)
        self.remove()
        pass


class QuestKill(BaseQuest):
    """A basic kill quest, procs off any kill."""

    key = "kill"
    goals = {"kill": 2}


class QuestHiveKill(QuestKill):
    """Test quest to kill a hive knight. Randomizes amount on application"""

    key = "hivekill"
    goals = {"kill": 1}

    def conditional(self, *args, **kwargs):
        return super().conditional(*args, **kwargs)


class QuestHandler(BuffHandlerExtended):
    """
    A handler for all quests and bounties. Uses the buff system under the hood, so utilizes all standard buff methods and behaviors.
    """

    def __init__(self, owner=None, dbkey="quests", autopause=False):
        super().__init__(owner, dbkey, autopause)
