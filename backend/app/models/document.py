"""Document database model for RAG"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Document(Base):
    """Document model for RAG knowledge base"""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Organization relationship
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    organization = relationship("Organization", back_populates="documents")

    # File information
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)  # MIME type
    size_bytes = Column(Integer, nullable=False)
    storage_path = Column(String, nullable=False)  # S3/MinIO key

    # Processing status
    processed = Column(Boolean, default=False, nullable=False)
    processing_error = Column(String, nullable=True)

    # Vector embeddings references
    chunk_ids = Column(ARRAY(String), default=list)  # References to vector DB
    chunk_count = Column(Integer, default=0)

    # Uploaded by
    upload_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    uploaded_by_user = relationship("User", back_populates="documents", foreign_keys=[upload_user_id])

    # Metadata
    metadata = Column(JSONB, default=dict)  # source, author, date, custom fields

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Soft delete
    deleted_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Document {self.filename}>"
