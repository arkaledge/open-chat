"""Conversation and message schemas"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, UUID4


class MessageBase(BaseModel):
    """Base message schema"""
    role: str = Field(..., pattern="^(system|user|assistant|function)$")
    content: str


class MessageCreate(MessageBase):
    """Schema for creating a message"""
    conversation_id: Optional[UUID4] = None


class MessageResponse(MessageBase):
    """Schema for message response"""
    id: UUID4
    conversation_id: UUID4
    model: Optional[str]
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    metadata: Dict[str, Any]
    feedback_score: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    """Base conversation schema"""
    title: str


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation"""
    model: str
    workspace_id: Optional[UUID4] = None


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation"""
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationResponse(ConversationBase):
    """Schema for conversation response"""
    id: UUID4
    user_id: UUID4
    workspace_id: Optional[UUID4]
    model: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    """Schema for chat message in request"""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Schema for chat completion request (OpenAI compatible)"""
    model: str
    messages: List[ChatMessage]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    stream: bool = False
    conversation_id: Optional[UUID4] = None

    # Extended features
    rag_enabled: bool = False
    web_search: bool = False
    tools: Optional[List[Dict[str, Any]]] = None


class ChatChoice(BaseModel):
    """Schema for chat choice in response"""
    index: int
    message: ChatMessage
    finish_reason: str


class ChatUsage(BaseModel):
    """Schema for token usage"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float = 0.0


class ChatResponse(BaseModel):
    """Schema for chat completion response (OpenAI compatible)"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: ChatUsage
