from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

class DocumentResponse(BaseModel):
    """Réponse pour un document"""
    doc_id: str
    filename: str
    file_size: int
    mime_type: str
    status: DocumentStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    metadata: Optional[Dict] = None

class DocumentListResponse(BaseModel):
    """Liste de documents"""
    documents: List[DocumentResponse]
    total: int
    skip: int
    limit: int

class DocumentUploadResponse(BaseModel):
    """Réponse d'upload de document"""
    doc_id: str
    filename: str
    message: str
    upload_url: Optional[str] = None
