from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class BatchStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BatchFileResult(BaseModel):
    """Résultat d'un fichier dans un batch"""
    filename: str
    status: str
    ocr_result: Optional[Dict] = None
    error: Optional[str] = None

class BatchCreateResponse(BaseModel):
    """Réponse de création de batch"""
    batch_id: str
    file_count: int
    status: BatchStatus
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BatchStatusResponse(BaseModel):
    """Statut d'un batch"""
    batch_id: str
    status: BatchStatus
    progress: float
    total_files: int
    processed_files: int
    failed_files: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class BatchListResponse(BaseModel):
    """Liste de batchs"""
    batches: List[BatchStatusResponse]
    total: int