from dataclasses import dataclass
from typeclasses.objects import Object
from typeclasses.characters import Character


@dataclass
class StatContext:
    base: int | float = 0
    bonus: int | float = 0
    total: int | float = 0


@dataclass
class DamageContext:
    amount: int | float = 0
    modified: int | float = 0


@dataclass
class AttackContext:
    hit: StatContext
    dodge: StatContext
    damage: DamageContext
    div: int | float
    isHit: bool = False
    isCrit: bool = False


@dataclass
class CombatContext:
    attacker: Character = None
    defender: Character = None
    weapon: Object = None
    attacks: list[AttackContext] = []
    total: int | float = 0
    element: str = "neutral"
    overkill: int | float = 0


@dataclass
class EventContext:
    eid: str
    source: Object
    timestamp: float
    context: dict
