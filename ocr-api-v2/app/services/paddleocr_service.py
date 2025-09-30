import logging
from typing import List, Dict, Tuple
import numpy as np

try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False

from .base_ocr import BaseOCRService
from ..config import settings
from ..schemas.engine import EngineInfo

logger = logging.getLogger(__name__)

class PaddleOCRService(BaseOCRService):
    """Service PaddleOCR"""
    
    def __init__(self):
        super().__init__()
        self.engine_name = "paddleocr"
        self.ocr = None
        self.supports_gpu = settings.paddle_use_gpu
    
    async def initialize(self) -> bool:
        """Initialise PaddleOCR"""
        if not PADDLE_AVAILABLE:
            logger.warning("PaddleOCR n'est pas disponible")
            return False
        
        try:
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang=settings.paddle_lang,
                use_gpu=settings.paddle_use_gpu,
                show_log=False,
                det_db_thresh=settings.paddle_det_db_thresh,
                det_db_box_thresh=0.5
            )
            self.is_initialized = True
            logger.info("✅ PaddleOCR initialisé")
            return True
        except Exception as e:
            logger.error(f"Erreur initialisation PaddleOCR: {e}")
            return False
    
    async def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """Extrait le texte avec PaddleOCR"""
        if not self.is_initialized:
            raise RuntimeError("PaddleOCR non initialisé")
        
        try:
            result = self.ocr.ocr(image, cls=True)
            
            texts = []
            confidences = []
            
            if result and len(result) > 0:
                for line in result[0]:
                    if line and len(line) > 1:
                        text = line[1][0]
                        confidence = line[1][1]
                        texts.append(text)
                        confidences.append(confidence)
            
            full_text = ' '.join(texts)
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            return full_text, float(avg_confidence)
            
        except Exception as e:
            logger.error(f"Erreur extraction PaddleOCR: {e}")
            return "", 0.0
    
    async def extract_with_coordinates(self, image: np.ndarray) -> List[Dict]:
        """Extrait avec coordonnées"""
        if not self.is_initialized:
            raise RuntimeError("PaddleOCR non initialisé")
        
        try:
            result = self.ocr.ocr(image, cls=True)
            
            extractions = []
            
            if result and len(result) > 0:
                for line in result[0]:
                    if line and len(line) > 1:
                        bbox = line[0]  # Coordonnées
                        text = line[1][0]
                        confidence = line[1][1]
                        
                        # Conversion bbox en format standard
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
            logger.error(f"Erreur extraction coordonnées PaddleOCR: {e}")
            return []
    
    def get_info(self) -> EngineInfo:
        return EngineInfo(
            name="paddleocr",
            available=self.is_initialized,
            version="2.7.3",
            supports_gpu=self.supports_gpu,
            languages=["fr", "en", "ch"]
        )
