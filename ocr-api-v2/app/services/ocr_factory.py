# Import asyncio pour l'initialisation
import asyncio
"""
Factory pour gérer les moteurs OCR avec fallback intelligent
"""
import logging
import time
from typing import Optional, List, Tuple, Dict
import numpy as np

from .base_ocr import BaseOCRService
from .paddleocr_service import PaddleOCRService
from .easyocr_service import EasyOCRService
from .kraken_service import KrakenOCRService
from ..config import get_settings
from ..schemas.engine import EngineResult, EngineInfo

logger = logging.getLogger(__name__)
settings = get_settings()


class OCRFactory:
    """
    Factory pour gérer les moteurs OCR avec fallback intelligent
    """
    
    def __init__(self):
        self.engines: Dict[str, BaseOCRService] = {}
        self._initialize_engines_sync()  # ✅ CHANGÉ: version synchrone
    
    def _initialize_engines_sync(self):
        """Initialise tous les moteurs disponibles (version synchrone)"""
        logger.info("🔧 Initialisation des moteurs OCR...")
        
        # PaddleOCR
        if "paddleocr" in settings.available_engines:
            try:
                paddle = PaddleOCRService()
                # ✅ CHANGÉ: Appel synchrone direct
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(paddle.initialize())
                loop.close()
                
                if success:
                    self.engines["paddleocr"] = paddle
                    logger.info("✅ PaddleOCR disponible")
            except Exception as e:
                logger.warning(f"PaddleOCR non disponible: {e}")
        
        # EasyOCR
        if "easyocr" in settings.available_engines:
            try:
                easy = EasyOCRService()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(easy.initialize())
                loop.close()
                
                if success:
                    self.engines["easyocr"] = easy
                    logger.info("✅ EasyOCR disponible")
            except Exception as e:
                logger.warning(f"EasyOCR non disponible: {e}")
        
        # Kraken
        if "kraken" in settings.available_engines:
            try:
                kraken = KrakenOCRService()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(kraken.initialize())
                loop.close()
                
                if success:
                    self.engines["kraken"] = kraken
                    logger.info("✅ Kraken disponible")
            except Exception as e:
                logger.warning(f"Kraken non disponible: {e}")
        
        if not self.engines:
            logger.error("❌ Aucun moteur OCR disponible!")
        else:
            logger.info(f"✅ Moteurs disponibles: {list(self.engines.keys())}")
    
    def get_engine(self, engine_name: str) -> Optional[BaseOCRService]:
        """Récupère un moteur spécifique"""
        return self.engines.get(engine_name)
    
    def get_available_engines(self) -> List[str]:
        """Liste des moteurs disponibles"""
        return list(self.engines.keys())
    
    def get_engines_info(self) -> List[EngineInfo]:
        """Informations sur tous les moteurs"""
        return [engine.get_info() for engine in self.engines.values()]
    
    async def extract_with_fallback(
        self,
        image: np.ndarray,
        preferred_engine: str = "auto",
        enable_fallback: bool = True,
        fallback_engines: Optional[List[str]] = None
    ) -> Tuple[str, float, List[EngineResult]]:
        """
        Extrait le texte avec fallback automatique
        
        Returns:
            (texte, confiance, historique_moteurs)
        """
        engines_results = []
        
        # Déterminer l'ordre des moteurs
        if preferred_engine == "auto" or preferred_engine not in self.engines:
            engine_order = fallback_engines or settings.fallback_order
        else:
            engine_order = [preferred_engine]
            if enable_fallback and fallback_engines:
                engine_order.extend([e for e in fallback_engines if e != preferred_engine])
            elif enable_fallback:
                engine_order.extend([e for e in settings.fallback_order if e != preferred_engine])
        
        # Filtrer les moteurs disponibles
        engine_order = [e for e in engine_order if e in self.engines]
        
        if not engine_order:
            logger.error("Aucun moteur OCR disponible")
            return "", 0.0, []
        
        # Essayer chaque moteur
        for engine_name in engine_order:
            engine = self.engines[engine_name]
            start_time = time.time()
            
            try:
                logger.info(f"🔍 Tentative avec {engine_name}...")
                text, confidence = await engine.extract_text(image)
                processing_time = time.time() - start_time
                
                result = EngineResult(
                    engine=engine_name,
                    success=True,
                    confidence=confidence,
                    processing_time=processing_time
                )
                engines_results.append(result)
                
                # Vérifier si le résultat est satisfaisant
                if confidence >= settings.confidence_threshold and len(text.strip()) > 0:
                    logger.info(f"✅ Succès avec {engine_name} (confiance: {confidence:.2f})")
                    return text, confidence, engines_results
                else:
                    logger.warning(f"⚠️  {engine_name} confiance faible ({confidence:.2f}), fallback...")
                    
            except Exception as e:
                processing_time = time.time() - start_time
                logger.error(f"❌ Erreur avec {engine_name}: {e}")
                
                result = EngineResult(
                    engine=engine_name,
                    success=False,
                    confidence=0.0,
                    processing_time=processing_time,
                    error=str(e)
                )
                engines_results.append(result)
            
            # Si fallback désactivé, s'arrêter après le premier moteur
            if not enable_fallback:
                break
        
        # Si tous les moteurs ont échoué, retourner le meilleur résultat
        best_result = max(engines_results, key=lambda x: x.confidence, default=None)
        if best_result and best_result.confidence > 0:
            # Ré-extraire le texte du meilleur moteur
            best_engine = self.engines[best_result.engine]
            text, confidence = await best_engine.extract_text(image)
            return text, confidence, engines_results
        
        return "", 0.0, engines_results


# Instance globale
_ocr_factory_instance: Optional[OCRFactory] = None


def get_ocr_factory() -> OCRFactory:
    """Récupère l'instance de la factory (Singleton)"""
    global _ocr_factory_instance
    if _ocr_factory_instance is None:
        _ocr_factory_instance = OCRFactory()
    return _ocr_factory_instance