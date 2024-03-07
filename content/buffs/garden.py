from components.buffsextended import BaseBuffExtended, BuffHandlerExtended, Mod


def rainbowfy(string: str):
    colortable = [
        "|500",
        "|520",
        "|250",
        "|252",
        "|052",
        "|025",
        "|005",
        "|025",
        "|052",
        "|252",
        "|250",
        "|520",
    ]
    bluetable = [
        "|055",
        "|045",
        "|035",
        "|025",
        "|015",
        "|005",
        "|015",
        "|025",
        "|035",
        "|045",
    ]
    split: list = list(string)
    rainbow = [bluetable[i % 10] + x for i, x in enumerate(split)]
    joined = "".join(rainbow)
    return joined


class ConsecratedEyes(BaseBuffExtended):
    key = "consecratedeyes"
    name = "Eyes of Consecration"
    flavor = "The intense red eyes gaze upon morbid ontologies."

    stacks = 13
    maxstacks = 13

    triggers = ["attacked"]

    vulnerable = False
    cache = {"vulnerable": False}

    def at_trigger(self, triggers: list[str], damage=0, attacker=None, *args, **kwargs):
        kwargs.update({"attacker": attacker, "damage": damage})
        if not self.vulnerable:
            if self.stacks > 1:
                if damage >= 1:
                    self.remove(1, context=kwargs)
            else:
                self.vulnerable = True
                message = "|035" + "A burst of energy shatters calcified steel!"
                attacker.location.msg_contents(message)
                self.owner.buffs.add(ConsecratedRegenerating)
        else:
            return

    def at_remove(self, attacker, *args, **kwargs):
        message = rainbowfy("An eye pops into ephemeric fractilline.")
        attacker.location.msg_contents(message)


class ConsecratedImmune(BaseBuffExtended):
    key = "consecratedimmune"
    name = "Armor of Consecration"
    flavor = "Steel laid still for eons."

    mods = [Mod("injury", "custom", 0)]

    def conditional(self, *args, **kwargs):
        eyes: ConsecratedEyes = self.handler.get("consecratedeyes")
        return not eyes.vulnerable

    def custom_modifier(self, value, *args, **kwargs):
        val = value * 0
        return val


class ConsecratedRegenerating(BaseBuffExtended):
    key = "consecratedregen"
    name = "Consecrated Armoring"
    flavor = "Steel grows like vines around vulnerable components."

    duration = 30

    def at_expire(self, *args, **kwargs):
        self.owner.location.msg_contents(
            "Rigid plating regrows to cover the Consecrated Mind!"
        )
        self.owner.buffs.add(ConsecratedEyes, stacks=12)
