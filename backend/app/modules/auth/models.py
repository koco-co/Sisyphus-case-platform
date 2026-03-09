import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import Base, BaseModel, TimestampMixin

# ── Permission matrix ────────────────────────────────────────────
# Maps role → set of allowed actions.
# Actions use "<module>:<verb>" format.
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {"*"},  # superuser
    "pm": {
        "products:read",
        "products:write",
        "requirements:read",
        "requirements:write",
        "diagnosis:read",
        "diagnosis:write",
        "scene_map:read",
        "scene_map:write",
        "generation:read",
        "generation:write",
        "testcases:read",
        "testcases:write",
        "export:read",
        "analytics:read",
        "knowledge:read",
        "knowledge:write",
        "coverage:read",
    },
    "tester": {
        "products:read",
        "requirements:read",
        "diagnosis:read",
        "scene_map:read",
        "scene_map:write",
        "generation:read",
        "generation:write",
        "testcases:read",
        "testcases:write",
        "execution:read",
        "execution:write",
        "export:read",
        "analytics:read",
        "knowledge:read",
        "coverage:read",
    },
    "dev": {
        "products:read",
        "requirements:read",
        "diagnosis:read",
        "testcases:read",
        "execution:read",
        "analytics:read",
        "knowledge:read",
    },
    "viewer": {
        "products:read",
        "requirements:read",
        "testcases:read",
        "analytics:read",
    },
}


def has_permission(role: str, action: str) -> bool:
    """Check if a role has a given action permission."""
    perms = ROLE_PERMISSIONS.get(role, set())
    return "*" in perms or action in perms


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[str] = mapped_column(String(20), default="member")


class Role(BaseModel):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(200))


class UserRole(Base, TimestampMixin):
    """Association between users and roles (many-to-many)."""

    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id"), index=True)
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=True, index=True
    )
