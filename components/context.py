from dataclasses import dataclass, field, fields


@dataclass
class BaseContext:
    pass


@dataclass
class StatContext:
    base: int | float = 0
    bonus: int | float = 0
    total: int | float = 0


def asdict_shallow(dc) -> dict:
    """Does a shallow conversion of dataclass to dict.

    Should be used instead of asdict on any dataclasses which store game object
    references and not just literals, as the database connection makes
    asdict mad."""
    r = dict((field.name, getattr(dc, field.name)) for field in fields(dc))
    return r


def congen(clist: list) -> dict:
    """Performs asdict_shallow on a list of dataclasses, and then combines them.

    Will overwrite values of the same name so you should use this mainly for dataclasses
    with no intersection keys or with values you want to overwrite.

    Used here to generate "contexts" for use in game systems"""

    return_dict = {}
    for context in clist:
        return_dict.update(asdict_shallow(context))

    return return_dict
