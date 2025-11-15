"""User database model"""

from datetime import datetime
from typing import List
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Table, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.base import Base


class UserRole(str, enum.Enum):
    """User roles enum"""
    ADMIN = "admin"
    WORKSPACE_OWNER = "workspace_owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class UserStatus(str, enum.Enum):
    """User status enum"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


# Association table for user-workspace many-to-many relationship
user_workspace = Table(
    'user_workspace',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE')),
    Column('workspace_id', UUID(as_uuid=True), ForeignKey('workspaces.id', ondelete='CASCADE')),
    Column('role', SQLEnum(UserRole), nullable=False, default=UserRole.EDITOR),
    Column('created_at', DateTime, default=datetime.utcnow)
)


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)

    # Organization relationship
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    organization = relationship("Organization", back_populates="users")

    # Workspace relationships
    workspaces = relationship(
        "Workspace",
        secondary=user_workspace,
        back_populates="users"
    )

    # Roles and permissions
    roles = Column(ARRAY(String), default=list)

    # User preferences
    preferences = Column(JSONB, default=dict)

    # Status and metadata
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # OAuth fields
    oauth_provider = Column(String, nullable=True)
    oauth_id = Column(String, nullable=True)

    # Email verification
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String, nullable=True)

    # Password reset
    password_reset_token = Column(String, nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="uploaded_by_user", foreign_keys="Document.upload_user_id")

    def __repr__(self) -> str:
        return f"<User {self.email}>"
