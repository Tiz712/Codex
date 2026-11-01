"""Authored simulation fixture; no AI, mesh or physical print claims."""
from dataclasses import dataclass, field

FORMS = frozenset({'folded', 'umbrella', 'shield', 'staff'})
EDGES = frozenset({('folded', 'umbrella'), ('umbrella', 'folded'),
                   ('umbrella', 'shield'), ('shield', 'umbrella'),
                   ('umbrella', 'staff'), ('staff', 'umbrella')})
RECIPES = {
    'guardian': ({'guardian_rune': 3, 'shield_fragment': 6}, 'shield'),
    'arcane': ({'arcane_fiber': 4, 'starlight_core': 1}, 'staff'),
}


class DomainError(ValueError):
    pass


@dataclass
class Session:
    current: str = 'folded'
    unlocked: set[str] = field(default_factory=lambda: {'folded', 'umbrella'})
    inventory: dict[str, int] = field(default_factory=dict)
    requests: dict[str, str] = field(default_factory=dict)

    def transition(self, target: str):
        if target not in FORMS:
            raise DomainError('UNKNOWN_FORM')
        if target not in self.unlocked:
            raise DomainError('FORM_LOCKED')
        if (self.current, target) not in EDGES:
            raise DomainError('TRANSITION_NOT_ALLOWED')
        self.current = target

    def craft(self, recipe_id: str, request_id: str):
        if not request_id:
            raise DomainError('REQUEST_ID_REQUIRED')
        if request_id in self.requests:
            if self.requests[request_id] != recipe_id:
                raise DomainError('IDEMPOTENCY_CONFLICT')
            return
        if recipe_id not in RECIPES:
            raise DomainError('UNKNOWN_RECIPE')
        materials, target = RECIPES[recipe_id]
        if target in self.unlocked:
            raise DomainError('ALREADY_UNLOCKED')
        if any(self.inventory.get(key, 0) < count for key, count in materials.items()):
            raise DomainError('INSUFFICIENT_MATERIALS')
        updated = self.inventory.copy()
        for key, count in materials.items():
            updated[key] -= count
        self.inventory = updated
        self.unlocked.add(target)
        self.requests[request_id] = recipe_id
