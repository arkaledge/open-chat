"""Conversation and Message database models"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Conversation(Base):
    """Conversation model"""
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # User and workspace relationships
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    user = relationship("User", back_populates="conversations")

    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey('workspaces.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    workspace = relationship("Workspace", back_populates="conversations")

    # Conversation details
    title = Column(String, nullable=False, default="New Conversation")
    model = Column(String, nullable=False)  # Primary model used

    # Metadata
    metadata = Column(JSONB, default=dict)  # tags, folder, sharing settings

    # Branching/Threading support
    parent_conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey('conversations.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    branched_at_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey('messages.id', ondelete='SET NULL'),
        nullable=True
    )
    branch_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Soft delete
    archived = Column(DateTime, nullable=True)

    # Relationships
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
        foreign_keys="Message.conversation_id"
    )

    # Branch relationships
    parent_conversation = relationship(
        "Conversation",
        remote_side=[id],
        backref="child_branches",
        foreign_keys=[parent_conversation_id]
    )

    branched_at_message = relationship(
        "Message",
        foreign_keys=[branched_at_message_id]
    )

    def __repr__(self) -> str:
        return f"<Conversation {self.title}>"


class Message(Base):
    """Message model"""
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Conversation relationship
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey('conversations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    conversation = relationship("Conversation", back_populates="messages")

    # Message content
    role = Column(String, nullable=False)  # system, user, assistant, function
    content = Column(Text, nullable=False)

    # Threading support
    parent_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey('messages.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    thread_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Root message of thread
    is_thread_root = Column(Integer, default=False, nullable=False)
    branch_depth = Column(Integer, default=0, nullable=False)  # How deep in branch tree

    # Model information
    model = Column(String, nullable=True)  # Specific model used for this message

    # Token usage
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # Cost tracking
    estimated_cost = Column(Float, default=0.0)

    # Metadata
    metadata = Column(JSONB, default=dict)  # sources, function calls, tool usage

    # Quality metrics
    feedback_score = Column(Integer, nullable=True)  # User feedback: 1 (thumbs up), -1 (thumbs down)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Thread relationships
    parent_message = relationship(
        "Message",
        remote_side=[id],
        backref="child_messages",
        foreign_keys=[parent_message_id]
    )

    def __repr__(self) -> str:
        return f"<Message {self.role}: {self.content[:50]}...>"
