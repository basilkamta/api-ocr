import logging
from typing import List, Dict, Tuple
import numpy as np
from PIL import Image

try:
    from kraken import binarization, pageseg, rpred
    from kraken.lib import models
    KRAKEN_AVAILABLE = True
except ImportError:
    KRAKEN_AVAILABLE = False

from .base_ocr import BaseOCRService
from ..config import settings
from ..schemas.engine import EngineInfo

logger = logging.getLogger(__name__)

class KrakenOCRService(BaseOCRService):
    """Service Kraken OCR"""
    
    def __init__(self):
        super().__init__()
        self.engine_name = "kraken"
        self.model = None
        self.supports_gpu = False  # Kraken CPU par défaut
    
    async def initialize(self) -> bool:
        """Initialise Kraken"""
        if not KRAKEN_AVAILABLE:
            logger.warning("Kraken n'est pas disponible")
            return False
        
        try:
            # Chargement du modèle français
            # Note: Le modèle doit être téléchargé au préalable
            # kraken get fr_best.mlmodel
            self.model = models.load_any(settings.kraken_model)
            self.is_initialized = True
            logger.info("✅ Kraken initialisé")
            return True
        except Exception as e:
            logger.error(f"Erreur initialisation Kraken: {e}")
            logger.info("💡 Téléchargez le modèle: kraken get fr_best.mlmodel")
            return False
    
    async def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """Extrait le texte avec Kraken"""
        if not self.is_initialized:
            raise RuntimeError("Kraken non initialisé")
        
        try:
            # Conversion en PIL Image
            pil_image = Image.fromarray(image)
            
            # Binarisation
            bw_image = binarization.nlbin(pil_image)
            
            # Segmentation
            seg = pageseg.segment(bw_image)
            
            # Reconnaissance
            results = rpred.rpred(self.model, bw_image, seg)
            
            texts = []
            confidences = []
            
            for record in results:
                texts.append(record.prediction)
                # Kraken retourne la confiance moyenne
                confidences.append(record.confidence)
            
            full_text = ' '.join(texts)
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            return full_text, float(avg_confidence)
            
        except Exception as e:
            logger.error(f"Erreur extraction Kraken: {e}")
            return "", 0.0
    
    async def extract_with_coordinates(self, image: np.ndarray) -> List[Dict]:
        """Extrait avec coordonnées"""
        if not self.is_initialized:
            raise RuntimeError("Kraken non initialisé")
        
        try:
            pil_image = Image.fromarray(image)
            bw_image = binarization.nlbin(pil_image)
            seg = pageseg.segment(bw_image)
            results = rpred.rpred(self.model, bw_image, seg)
            
            extractions = []
            
            for record in results:
                bbox = record.bbox
                
                extractions.append({
                    'text': record.prediction,
                    'confidence': record.confidence,
                    'bbox': {
                        'x': int(bbox[0]),
                        'y': int(bbox[1]),
                        'width': int(bbox[2] - bbox[0]),
                        'height': int(bbox[3] - bbox[1])
                    }
                })
            
            return extractions
            
        except Exception as e:
            logger.error(f"Erreur extraction coordonnées Kraken: {e}")
            return []
    
    def get_info(self) -> EngineInfo:
        return EngineInfo(
            name="kraken",
            available=self.is_initialized,
            version="4.3.13",
            supports_gpu=False,
            languages=["fr", "en", "la"]
        )