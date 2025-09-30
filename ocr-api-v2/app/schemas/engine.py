from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class EngineStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    INITIALIZING = "initializing"

class EngineInfo(BaseModel):
    """Information sur un moteur OCR"""
    name: str
    available: bool
    version: Optional[str] = None
    supports_gpu: bool
    languages: List[str]
    status: EngineStatus = EngineStatus.AVAILABLE

class EnginesListResponse(BaseModel):
    """Liste des moteurs disponibles"""
    engines: List[EngineInfo]
    default_engine: str
    fallback_enabled: bool

class EngineResult(BaseModel):
    """Résultat d'un moteur OCR"""
    engine: str
    success: bool
    confidence: float
    processing_time: float
    error: Optional[str] = None

class EngineTestResponse(BaseModel):
    """Réponse du test d'un moteur"""
    engine: str
    success: bool
    message: str
    text: Optional[str] = None
    confidence: Optional[float] = None
    processing_time: Optional[float] = None