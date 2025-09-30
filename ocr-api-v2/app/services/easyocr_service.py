import logging
from typing import List, Dict, Tuple
import numpy as np

try:
    import easyocr
    EASY_AVAILABLE = True
except ImportError:
    EASY_AVAILABLE = False

from .base_ocr import BaseOCRService
from ..config import settings
from ..schemas.engine import EngineInfo

logger = logging.getLogger(__name__)

class EasyOCRService(BaseOCRService):
    """Service EasyOCR"""
    
    def __init__(self):
        super().__init__()
        self.engine_name = "easyocr"
        self.reader = None
        self.supports_gpu = settings.easy_use_gpu
    
    async def initialize(self) -> bool:
        """Initialise EasyOCR"""
        if not EASY_AVAILABLE:
            logger.warning("EasyOCR n'est pas disponible")
            return False
        
        try:
            self.reader = easyocr.Reader(
                settings.easy_languages,
                gpu=settings.easy_use_gpu,
                verbose=False
            )
            self.is_initialized = True
            logger.info("✅ EasyOCR initialisé")
            return True
        except Exception as e:
            logger.error(f"Erreur initialisation EasyOCR: {e}")
            return False
    
    async def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """Extrait le texte avec EasyOCR"""
        if not self.is_initialized:
            raise RuntimeError("EasyOCR non initialisé")
        
        try:
            results = self.reader.readtext(image, detail=1, paragraph=False)
            
            texts = []
            confidences = []
            
            for (bbox, text, confidence) in results:
                if confidence > settings.confidence_threshold:
                    texts.append(text)
                    confidences.append(confidence)
            
            full_text = ' '.join(texts)
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            return full_text, float(avg_confidence)
            
        except Exception as e:
            logger.error(f"Erreur extraction EasyOCR: {e}")
            return "", 0.0
    
    async def extract_with_coordinates(self, image: np.ndarray) -> List[Dict]:
        """Extrait avec coordonnées"""
        if not self.is_initialized:
            raise RuntimeError("EasyOCR non initialisé")
        
        try:
            results = self.reader.readtext(image, detail=1)
            
            extractions = []
            
            for (bbox, text, confidence) in results:
                if confidence > settings.confidence_threshold:
                    # bbox est [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]
                    
                    extractions.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': {
                            'x': int(min(x_coords)),
                            'y': int(min(y_coords)),
                            'width': int(max(x_coords) - min(x_coords)),
                            'height': int(max(y_coords) - min(y_coords))
                        }
                    })
            
            return extractions
            
        except Exception as e:
            logger.error(f"Erreur extraction coordonnées EasyOCR: {e}")
            return []
    
    def get_info(self) -> EngineInfo:
        return EngineInfo(
            name="easyocr",
            available=self.is_initialized,
            version="1.7.1",
            supports_gpu=self.supports_gpu,
            languages=settings.easy_languages
        )
