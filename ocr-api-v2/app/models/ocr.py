from sqlalchemy import Column, String, Integer, Float, Text, Boolean, JSON
from .base import TimeStampedModel
import uuid

class OCRResult(TimeStampedModel):
    """Résultat d'extraction OCR"""
    __tablename__ = "ocr_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_hash = Column(String, unique=True, index=True, nullable=False)
    filename = Column(String, nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String)
    
    # Moteur OCR
    primary_engine = Column(String)
    engines_used = Column(JSON)  # Liste des moteurs essayés
    fallback_triggered = Column(Boolean, default=False)
    
    # Résultats
    success = Column(Boolean, default=False)
    confidence_score = Column(Float)
    processing_time = Column(Float)
    
    # Données extraites
    extracted_data = Column(JSON)
    raw_text = Column(Text)
    
    # Métadonnées
    preprocessing_applied = Column(JSON)
    image_quality = Column(Float)
    
    # Relations
    # document_id = Column(String, ForeignKey('documents.id'))