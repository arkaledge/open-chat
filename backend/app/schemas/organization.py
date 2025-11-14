"""Organization schemas"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, UUID4


class OrganizationBase(BaseModel):
    """Base organization schema"""
    name: str
    domain: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization"""
    plan: str = "free"


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization"""
    name: Optional[str] = None
    domain: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class OrganizationResponse(OrganizationBase):
    """Schema for organization response"""
    id: UUID4
    plan: str
    subscription_status: str
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
