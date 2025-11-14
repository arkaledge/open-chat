"""Document schemas"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, UUID4


class DocumentBase(BaseModel):
    """Base document schema"""
    filename: str
    content_type: str


class DocumentCreate(DocumentBase):
    """Schema for creating a document"""
    organization_id: UUID4
    metadata: Optional[Dict[str, Any]] = None


class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(DocumentBase):
    """Schema for document response"""
    id: UUID4
    organization_id: UUID4
    size_bytes: int
    processed: bool
    processing_error: Optional[str]
    chunk_count: int
    upload_user_id: Optional[UUID4]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class DocumentSearchRequest(BaseModel):
    """Schema for document search request"""
    query: str
    organization_id: UUID4
    limit: int = Field(default=5, ge=1, le=50)
    filters: Optional[Dict[str, Any]] = None


class DocumentSearchResult(BaseModel):
    """Schema for document search result"""
    document_id: UUID4
    filename: str
    chunk_text: str
    score: float
    metadata: Dict[str, Any]
