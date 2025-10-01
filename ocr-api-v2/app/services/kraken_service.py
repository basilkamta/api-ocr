import logging
from typing import List, Dict, Tuple
import numpy as np
from PIL import Image
from pathlib import Path

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
            model_path = Path(settings.kraken_model)
            
            # ✅ Vérifier si le modèle existe
            if not model_path.exists():
                logger.warning(f"Modèle Kraken non trouvé: {model_path}")
                logger.info("💡 Téléchargement du modèle...")
                
                # Télécharger le modèle
                success = await self._download_model(model_path)
                if not success:
                    logger.error("Échec du téléchargement du modèle Kraken")
                    return False
            
            # Chargement du modèle
            logger.info(f"Chargement du modèle Kraken: {model_path}")
            self.model = models.load_any(str(model_path))
            
            self.is_initialized = True
            logger.info("✅ Kraken initialisé")
            return True
            
        except Exception as e:
            logger.error(f"Erreur initialisation Kraken: {e}")
            return False
    
    async def _download_model(self, model_path: Path) -> bool:
        """
        Télécharge le modèle Kraken français
        
        Args:
            model_path: Chemin où sauvegarder le modèle
        
        Returns:
            True si succès
        """
        try:
            import urllib.request
            
            # Créer le répertoire parent
            model_path.parent.mkdir(parents=True, exist_ok=True)
            
            # URL du modèle français
            # Alternative: utiliser kraken get fr_best.mlmodel
            url = "https://github.com/mittagessen/kraken/raw/main/models/fr_best.mlmodel"
            
            logger.info(f"📥 Téléchargement depuis: {url}")
            
            # Télécharger
            urllib.request.urlretrieve(url, str(model_path))
            
            if model_path.exists() and model_path.stat().st_size > 0:
                logger.info(f"✅ Modèle téléchargé: {model_path}")
                return True
            else:
                logger.error("Le fichier téléchargé est vide ou inexistant")
                return False
                
        except Exception as e:
            logger.error(f"Erreur téléchargement modèle Kraken: {e}")
            
            # Méthode alternative: utiliser kraken CLI
            try:
                import subprocess
                logger.info("Tentative avec kraken CLI...")
                
                result = subprocess.run(
                    ["kraken", "get", "fr_best.mlmodel"],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes max
                )
                
                if result.returncode == 0:
                    # Déplacer le modèle au bon endroit
                    import shutil
                    # kraken télécharge dans ~/.kraken
                    home_model = Path.home() / ".kraken" / "fr_best.mlmodel"
                    if home_model.exists():
                        shutil.copy(home_model, model_path)
                        logger.info(f"✅ Modèle copié: {model_path}")
                        return True
                
                logger.error(f"Erreur kraken CLI: {result.stderr}")
                return False
                
            except Exception as e2:
                logger.error(f"Erreur méthode alternative: {e2}")
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