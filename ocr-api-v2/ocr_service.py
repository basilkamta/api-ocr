import re
import time
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import numpy as np
import cv2
from PIL import Image

# Import PaddleOCR
try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False
    print("⚠️  PaddleOCR non disponible")

from .config import settings
from .models import OCRRequest, OCRResponse, DocumentInfo

logger = logging.getLogger(__name__)

class OCRService:
    """Service OCR avec PaddleOCR"""
    
    def __init__(self):
        if not PADDLE_AVAILABLE:
            raise RuntimeError("PaddleOCR n'est pas installé")
        
        # Initialisation de PaddleOCR
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang=settings.default_lang,
            use_gpu=settings.use_gpu,
            show_log=False,
            det_db_thresh=settings.det_db_thresh,
            det_db_box_thresh=settings.det_db_box_thresh
        )
        
        # Patterns d'extraction
        self.patterns = {
            'mandat': [
                r'MD[/\\](\d{7})',
                r'N°\s*Mandat[:\s]*MD[/\\](\d{7})',
            ],
            'bordereau': [
                r'BOR[/\\](\d{7})',
                r'N°\s*Bordereau[:\s]*BOR[/\\](\d{7})',
            ],
            'exercice': [
                r'Exercice[:\s]*(\d{4})',
                r'(\d{4})',
            ]
        }
        
        logger.info("✅ OCRService initialisé avec PaddleOCR")
    
    async def process_document(self, image_path: Path, params: OCRRequest) -> OCRResponse:
        """Traite un document et extrait les métadonnées"""
        start_time = time.time()
        
        try:
            # 1. Charger et prétraiter l'image
            image = self._load_image(image_path)
            processed_image = self._preprocess_image(image)
            
            # 2. OCR avec PaddleOCR
            ocr_result = self.ocr.ocr(processed_image, cls=True)
            
            # 3. Extraire le texte
            full_text = self._extract_text_from_result(ocr_result)
            avg_confidence = self._calculate_confidence(ocr_result)
            
            # 4. Extraire les métadonnées
            metadata = self._extract_metadata(full_text, params)
            
            # 5. Construire la réponse
            return OCRResponse(
                success=bool(metadata['mandat'] or metadata['bordereau']),
                processing_time=time.time() - start_time,
                engine_used="paddleocr",
                mandat=metadata['mandat'],
                bordereau=metadata['bordereau'],
                exercice=metadata['exercice'],
                raw_text=full_text[:500],  # Limité pour éviter gros logs
                confidence_score=avg_confidence
            )
            
        except Exception as e:
            logger.error(f"Erreur traitement OCR: {e}")
            return OCRResponse(
                success=False,
                processing_time=time.time() - start_time,
                engine_used="paddleocr",
                raw_text=f"Erreur: {str(e)}"
            )
    
    def _load_image(self, image_path: Path) -> np.ndarray:
        """Charge une image depuis un chemin"""
        if not image_path.exists():
            raise FileNotFoundError(f"Image non trouvée: {image_path}")
        
        # Charger avec OpenCV
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Impossible de charger l'image: {image_path}")
        
        return image
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocessing simple de l'image"""
        # Conversion en RGB (PaddleOCR préfère RGB)
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        else:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        return image
    
    def _extract_text_from_result(self, ocr_result) -> str:
        """Extrait le texte depuis le résultat PaddleOCR"""
        texts = []
        
        if ocr_result and len(ocr_result) > 0:
            for line in ocr_result[0]:
                if line and len(line) > 1:
                    text = line[1][0]  # Le texte est dans line[1][0]
                    texts.append(text)
        
        return ' '.join(texts)
    
    def _calculate_confidence(self, ocr_result) -> float:
        """Calcule la confiance moyenne"""
        confidences = []
        
        if ocr_result and len(ocr_result) > 0:
            for line in ocr_result[0]:
                if line and len(line) > 1:
                    confidence = line[1][1]  # La confiance est dans line[1][1]
                    confidences.append(confidence)
        
        return np.mean(confidences) if confidences else 0.0
    
    def _extract_metadata(self, text: str, params: OCRRequest) -> Dict:
        """Extrait les métadonnées depuis le texte"""
        metadata = {
            'mandat': None,
            'bordereau': None,
            'exercice': None
        }
        
        # Extraction mandat
        if params.extract_mandat:
            metadata['mandat'] = self._extract_document_type(text, 'mandat')
        
        # Extraction bordereau
        if params.extract_bordereau:
            metadata['bordereau'] = self._extract_document_type(text, 'bordereau')
        
        # Extraction exercice
        if params.extract_exercice:
            metadata['exercice'] = self._extract_exercice(text)
        
        return metadata
    
    def _extract_document_type(self, text: str, doc_type: str) -> Optional[DocumentInfo]:
        """Extrait un type de document spécifique"""
        patterns = self.patterns.get(doc_type, [])
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                number = match.group(1) if match.groups() else match.group(0)
                
                if self._validate_format(number, doc_type):
                    prefix = "MD" if doc_type == "mandat" else "BOR"
                    full_ref = f"{prefix}/{number}"
                    
                    return DocumentInfo(
                        type=doc_type,
                        number=number,
                        full_reference=full_ref,
                        confidence=0.85
                    )
        
        return None
    
    def _extract_exercice(self, text: str) -> Optional[str]:
        """Extrait l'exercice fiscal"""
        patterns = self.patterns.get('exercice', [])
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                year = match.group(1) if match.groups() else match.group(0)
                if len(year) == 4 and 2015 <= int(year) <= 2030:
                    return year
        
        return None
    
    def _validate_format(self, number: str, doc_type: str) -> bool:
        """Valide le format d'un numéro"""
        if not number.isdigit():
            return False
        
        if doc_type in ['mandat', 'bordereau'] and len(number) == 7:
            year_prefix = number[:2]
            return year_prefix in ['24', '23', '22', '21', '20']
        
        return False

# Instance globale du service
_ocr_service_instance = None

def get_ocr_service() -> OCRService:
    """Récupère l'instance du service OCR (Singleton)"""
    global _ocr_service_instance
    if _ocr_service_instance is None:
        _ocr_service_instance = OCRService()
    return _ocr_service_instance