from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class OCRRequest(BaseModel):
    """Requête d'extraction OCR simple"""
    extract_mandat: bool = True
    extract_bordereau: bool = True
    extract_exercice: bool = True

class DocumentInfo(BaseModel):
    """Information extraite d'un document"""
    type: str
    number: str
    full_reference: str
    confidence: float

class OCRResponse(BaseModel):
    """Réponse d'extraction OCR"""
    success: bool
    processing_time: float
    engine_used: str
    mandat: Optional[DocumentInfo] = None
    bordereau: Optional[DocumentInfo] = None
    exercice: Optional[str] = None
    raw_text: str = ""
    confidence_score: float = 0.0

class HealthResponse(BaseModel):
    """Santé de l'API"""
    status: str
    version: str
    engine: str
    gpu_available: bool