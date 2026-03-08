from enum import StrEnum


class RequirementStatus(StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    DIAGNOSED = "diagnosed"
    GENERATING = "generating"
    COMPLETED = "completed"


class ScenarioType(StrEnum):
    NORMAL = "normal"
    EXCEPTION = "exception"
    BOUNDARY = "boundary"
    CONCURRENT = "concurrent"
    PERMISSION = "permission"


class SceneNodeSource(StrEnum):
    DOCUMENT = "document"
    AI_DETECTED = "ai_detected"
    USER_ADDED = "user_added"


class SceneNodeStatus(StrEnum):
    COVERED = "covered"
    SUPPLEMENTED = "supplemented"
    MISSING = "missing"
    PENDING = "pending"
    CONFIRMED = "confirmed"


class Priority(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class TestCaseStatus(StrEnum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    DEPRECATED = "deprecated"


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
