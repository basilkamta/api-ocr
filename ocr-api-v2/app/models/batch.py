from sqlalchemy import Column, String, Integer, Float, Enum as SQLEnum, JSON
from .base import TimeStampedModel
from ..schemas.batch import BatchStatus
import uuid

class Batch(TimeStampedModel):
    """Batch de traitement"""
    __tablename__ = "batches"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(SQLEnum(BatchStatus), default=BatchStatus.QUEUED)
    
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    progress = Column(Float, default=0.0)
    
    # Configuration
    engine = Column(String)
    options = Column(JSON)
    
    # Résultats
    results = Column(JSON)
    
    # Relations
    # user_id = Column(String, ForeignKey('users.id'))