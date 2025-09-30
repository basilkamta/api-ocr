from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class OCREngine(str, Enum):
    PADDLE = "paddleocr"
    EASY = "easyocr"
    KRAKEN = "kraken"
    AUTO = "auto"  # Sélection automatique

class ExtractionMode(str, Enum):
    FAST = "fast"
    STANDARD = "standard"
    ACCURATE = "accurate"

class OCRRequest(BaseModel):
    """Requête d'extraction OCR avancée"""
    # Moteur
    engine: OCREngine = OCREngine.AUTO
    enable_fallback: bool = True
    fallback_engines: Optional[List[str]] = None
    
    # Extraction
    extract_mandat: bool = True
    extract_bordereau: bool = True
    extract_exercice: bool = True
    extract_dates: bool = False
    extract_amounts: bool = False
    
    # Options
    mode: ExtractionMode = ExtractionMode.STANDARD
    confidence_threshold: float = 0.6

class DocumentInfo(BaseModel):
    """Information extraite"""
    type: str
    number: str
    full_reference: str
    confidence: float
    coordinates: Optional[Dict[str, int]] = None

class EngineResult(BaseModel):
    """Résultat d'un moteur OCR"""
    engine: str
    success: bool
    confidence: float
    processing_time: float
    error: Optional[str] = None

class OCRResponse(BaseModel):
    """Réponse d'extraction OCR complète"""
    success: bool
    processing_time: float
    
    # Moteur utilisé
    primary_engine: str
    engines_used: List[EngineResult]
    fallback_triggered: bool
    
    # Données extraites
    mandat: Optional[DocumentInfo] = None
    bordereau: Optional[DocumentInfo] = None
    exercice: Optional[str] = None
    dates: Optional[List[str]] = None
    amounts: Optional[List[float]] = None
    
    # Texte et qualité
    raw_text: str = ""
    confidence_score: float = 0.0
    
    # Metadata
    image_quality: Optional[float] = None
    preprocessing_applied: List[str] = []

class EngineInfo(BaseModel):
    """Informations sur un moteur OCR"""
    name: str
    available: bool
    version: Optional[str] = None
    supports_gpu: bool
    languages: List[str]

class EnginesListResponse(BaseModel):
    """Liste des moteurs disponibles"""
    engines: List[EngineInfo]
    default_engine: str
    fallback_enabled: bool