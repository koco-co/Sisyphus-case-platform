from app.common.audit import InMemoryAuditStore, write_publish_audit


def test_publish_writes_audit_log():
    store = InMemoryAuditStore()

    write_publish_audit(store, task_id=42, reviewer_id=7)

    assert store.last_event()['action'] == 'task.publish'
    assert store.last_event()['task_id'] == 42
    assert store.last_event()['reviewer_id'] == 7
