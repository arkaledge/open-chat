"""Branch and thread schemas"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, UUID4


class BranchCreate(BaseModel):
    """Schema for creating a conversation branch"""
    title: Optional[str] = None
    include_future_messages: bool = Field(
        default=False,
        description="Include messages after the branch point"
    )


class BranchInfo(BaseModel):
    """Information about a conversation branch"""
    conversation_id: UUID4
    parent_conversation_id: Optional[UUID4]
    branched_at_message_id: Optional[UUID4]
    branch_depth: int
    title: str
    created_at: datetime


class BranchTree(BaseModel):
    """Tree structure of conversation branches"""
    conversation_id: UUID4
    title: str
    created_at: datetime
    branches: List['BranchTree'] = []
    message_count: int


class ThreadMessage(BaseModel):
    """Message in a thread"""
    id: UUID4
    content: str
    role: str
    parent_message_id: Optional[UUID4]
    thread_id: Optional[UUID4]
    is_thread_root: bool
    branch_depth: int
    created_at: datetime
    replies: List['ThreadMessage'] = []


class MessageBranchRequest(BaseModel):
    """Request to branch from a specific message"""
    new_content: Optional[str] = Field(
        default=None,
        description="New content for the branching message (replaces original)"
    )
    model: Optional[str] = Field(
        default=None,
        description="Model to use for the branch (inherits from parent if not specified)"
    )
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)


class RegenerateMessageRequest(BaseModel):
    """Request to regenerate a message"""
    model: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    keep_original: bool = Field(
        default=True,
        description="Keep original message and create alternative"
    )


class MessageEdit(BaseModel):
    """Edit a message and regenerate response"""
    content: str
    regenerate_response: bool = Field(
        default=True,
        description="Regenerate assistant response after edit"
    )
    create_branch: bool = Field(
        default=True,
        description="Create a branch instead of modifying original"
    )


# Enable forward references
BranchTree.model_rebuild()
ThreadMessage.model_rebuild()
