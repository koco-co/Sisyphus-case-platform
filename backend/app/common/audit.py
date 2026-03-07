from dataclasses import dataclass, field
from typing import Any


@dataclass
class InMemoryAuditStore:
    events: list[dict[str, Any]] = field(default_factory=list)

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        self.events.append(event)
        return event

    def last_event(self) -> dict[str, Any]:
        return self.events[-1]


def write_publish_audit(store: InMemoryAuditStore, task_id: int, reviewer_id: int) -> dict[str, Any]:
    return store.append({
        'action': 'task.publish',
        'task_id': task_id,
        'reviewer_id': reviewer_id,
    })
