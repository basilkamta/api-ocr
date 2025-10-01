#!/usr/bin/env python3
"""
Script pour télécharger les modèles OCR nécessaires
"""
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def download_kraken_model():
    """Télécharge le modèle Kraken français"""
    try:
        from kraken import repo
        
        logger.info("📥 Téléchargement du modèle Kraken français...")
        
        # Créer le répertoire des modèles
        models_dir = Path("/app/models")
        models_dir.mkdir(exist_ok=True)
        
        # Télécharger le modèle
        # Les modèles disponibles : fr_best.mlmodel, fr_modern.mlmodel
        model_path = models_dir / "fr_best.mlmodel"
        
        if model_path.exists():
            logger.info(f"✅ Modèle déjà présent : {model_path}")
            return True
        
        logger.info("⏳ Téléchargement en cours (peut prendre quelques minutes)...")
        
        # Alternative: téléchargement direct
        import urllib.request
        url = "https://github.com/mittagessen/kraken/raw/main/models/fr_best.mlmodel"
        
        urllib.request.urlretrieve(url, str(model_path))
        
        logger.info(f"✅ Modèle téléchargé : {model_path}")
        return True
        
    except ImportError:
        logger.warning("⚠️  Kraken n'est pas installé, skip téléchargement")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur téléchargement modèle Kraken : {e}")
        return False

def download_paddleocr_models():
    """Vérifie/télécharge les modèles PaddleOCR"""
    try:
        from paddleocr import PaddleOCR
        
        logger.info("📥 Vérification des modèles PaddleOCR...")
        
        # PaddleOCR télécharge automatiquement les modèles au premier lancement
        # On fait juste un test d'initialisation
        ocr = PaddleOCR(
            use_angle_cls=True,
            lang='fr',
            use_gpu=False,
            show_log=False
        )
        
        logger.info("✅ Modèles PaddleOCR OK")
        return True
        
    except ImportError:
        logger.warning("⚠️  PaddleOCR n'est pas installé, skip")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur modèles PaddleOCR : {e}")
        return False

def download_easyocr_models():
    """Télécharge les modèles EasyOCR"""
    try:
        import easyocr
        
        logger.info("📥 Téléchargement des modèles EasyOCR...")
        
        # EasyOCR télécharge automatiquement les modèles
        reader = easyocr.Reader(['fr', 'en'], gpu=False, verbose=False)
        
        logger.info("✅ Modèles EasyOCR OK")
        return True
        
    except ImportError:
        logger.warning("⚠️  EasyOCR n'est pas installé, skip")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur modèles EasyOCR : {e}")
        return False

def main():
    """Télécharge tous les modèles nécessaires"""
    logger.info("🚀 Téléchargement des modèles OCR")
    logger.info("=" * 50)
    
    results = {
        'PaddleOCR': download_paddleocr_models(),
        'EasyOCR': download_easyocr_models(),
        'Kraken': download_kraken_model()
    }
    
    logger.info("\n" + "=" * 50)
    logger.info("📊 Résumé des téléchargements :")
    
    for engine, success in results.items():
        status = "✅" if success else "❌"
        logger.info(f"  {status} {engine}")
    
    all_success = all(results.values())
    
    if all_success:
        logger.info("\n✅ Tous les modèles sont prêts!")
        return 0
    else:
        logger.warning("\n⚠️  Certains modèles n'ont pas pu être téléchargés")
        return 1

if __name__ == "__main__":
    sys.exit(main())