from sqlalchemy import Column, String, Integer, Enum as SQLEnum
from .base import TimeStampedModel
from ..schemas.document import DocumentStatus
import uuid

class Document(TimeStampedModel):
    """Document uploadé"""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    original_filename = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    mime_type = Column(String)
    file_hash = Column(String, unique=True, index=True)
    
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING)
    
    # Métadonnées
    description = Column(String)
    tags = Column(String)  # JSON array
    
    # Relations
    # user_id = Column(String, ForeignKey('users.id'))
    # ocr_result_id = Column(String, ForeignKey('ocr_results.id'))