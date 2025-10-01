#!/usr/bin/env python3
"""
Script de test pour l'extraction OCR sur des mandats FEICOM réels
Utilise les PDF fournis pour valider l'extraction des métadonnées

Usage:
    python test_ocr_mandats.py --file mandat.pdf
    python test_ocr_mandats.py --directory ./mandats/
    python test_ocr_mandats.py --all  # teste tous les mandats dans ./test_documents/
"""

import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime
import time

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'ocr_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Imports des services OCR
try:
    from app.services.ocr_factory import get_ocr_factory
    from app.extractors.metadata_extractor import MetadataExtractor
    from app.utils.image_utils import ImagePreprocessor
    from app.config import get_settings
except ImportError as e:
    logger.error(f"Erreur import modules: {e}")
    logger.error("Assurez-vous d'être dans le répertoire ocr-api-v2/")
    sys.exit(1)

settings = get_settings()


# =================================================================
# DONNÉES DE TEST ATTENDUES (Ground Truth)
# =================================================================

GROUND_TRUTH = {
    "mandat_2404839.pdf": {
        "mandat": "2404839",
        "bordereau": "2401530",
        "exercice": "2024",
        "beneficiaire": "ETS DELFKA",
        "montant_total": 9301500,
        "dates": ["16/07/2024", "30/05/2024", "21/06/2024"]
    },
    "mandat_retenues.pdf": {
        "mandat": "2404839",
        "bordereau": "2401530",
        "exercice": "2024",
        "retenues": 1673100,
        "net_a_payer": 1673100
    }
}


class OCRTester:
    """Classe pour tester l'extraction OCR"""
    
    def __init__(self):
        self.factory = None
        self.extractor = MetadataExtractor()
        self.preprocessor = ImagePreprocessor()
        self.results = []
    
    async def initialize(self):
        """Initialise les moteurs OCR"""
        logger.info("🔧 Initialisation des moteurs OCR...")
        
        self.factory = get_ocr_factory()
        await self.factory.initialize_engines()
        
        available = self.factory.get_available_engines()
        logger.info(f"✅ Moteurs disponibles: {available}")
        
        if not available:
            raise RuntimeError("❌ Aucun moteur OCR disponible!")
    
    async def test_single_file(
        self,
        file_path: Path,
        engine: str = "auto",
        expected: Optional[Dict] = None
    ) -> Dict:
        """
        Teste l'extraction sur un fichier unique
        
        Args:
            file_path: Chemin vers le fichier
            engine: Moteur à utiliser
            expected: Données attendues (ground truth)
        
        Returns:
            Résultats du test
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"📄 Test du fichier: {file_path.name}")
        logger.info(f"{'='*70}")
        
        start_time = time.time()
        
        try:
            # 1. Conversion en image si PDF
            if file_path.suffix.lower() == '.pdf':
                logger.info("📑 Conversion PDF → Image...")
                image = self.preprocessor.pdf_to_image(str(file_path))
            else:
                import cv2
                image = cv2.imread(str(file_path))
            
            if image is None:
                raise ValueError(f"Impossible de charger l'image: {file_path}")
            
            logger.info(f"✅ Image chargée: {image.shape}")
            
            # 2. Preprocessing
            logger.info("🔧 Preprocessing de l'image...")
            processed_image = self.preprocessor.preprocess(image, mode="standard")
            
            # 3. Extraction OCR
            logger.info(f"🔍 Extraction OCR (moteur: {engine})...")
            text, confidence, engines_used = await self.factory.extract_with_fallback(
                processed_image,
                preferred_engine=engine,
                enable_fallback=True
            )
            
            processing_time = time.time() - start_time
            
            logger.info(f"✅ OCR terminé en {processing_time:.2f}s")
            logger.info(f"   Moteur(s): {[e.engine for e in engines_used]}")
            logger.info(f"   Confiance: {confidence:.2%}")
            logger.info(f"   Texte extrait: {len(text)} caractères")
            
            # 4. Extraction des métadonnées
            logger.info("📊 Extraction des métadonnées...")
            metadata = self.extractor.extract_all(text)
            
            # 5. Validation
            validation = self.extractor.validate_extraction(metadata)
            
            # 6. Affichage des résultats
            self._display_results(metadata, validation)
            
            # 7. Comparaison avec ground truth
            comparison = None
            if expected:
                comparison = self._compare_with_ground_truth(metadata, expected)
                self._display_comparison(comparison)
            
            # 8. Construction du résultat
            result = {
                'file': file_path.name,
                'success': True,
                'processing_time': processing_time,
                'engines_used': [e.engine for e in engines_used],
                'confidence': confidence,
                'text_length': len(text),
                'metadata': self._serialize_metadata(metadata),
                'validation': validation,
                'comparison': comparison,
                'timestamp': datetime.now().isoformat()
            }
            
            self.results.append(result)
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du test: {e}", exc_info=True)
            
            result = {
                'file': file_path.name,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
            self.results.append(result)
            return result
    
    async def test_directory(self, directory: Path, engine: str = "auto") -> List[Dict]:
        """Teste tous les fichiers d'un répertoire"""
        logger.info(f"\n{'='*70}")
        logger.info(f"📁 Test du répertoire: {directory}")
        logger.info(f"{'='*70}")
        
        # Trouver tous les PDFs et images
        patterns = ['*.pdf', '*.png', '*.jpg', '*.jpeg']
        files = []
        
        for pattern in patterns:
            files.extend(directory.glob(pattern))
        
        if not files:
            logger.warning(f"Aucun fichier trouvé dans {directory}")
            return []
        
        logger.info(f"📄 {len(files)} fichier(s) trouvé(s)")
        
        results = []
        for i, file_path in enumerate(files, 1):
            logger.info(f"\n[{i}/{len(files)}] Traitement de {file_path.name}...")
            
            # Récupérer les données attendues si disponibles
            expected = GROUND_TRUTH.get(file_path.name)
            
            result = await self.test_single_file(file_path, engine, expected)
            results.append(result)
            
            # Pause entre les fichiers
            if i < len(files):
                time.sleep(1)
        
        return results
    
    def _display_results(self, metadata: Dict, validation: Dict):
        """Affiche les résultats extraits"""
        logger.info("\n📋 RÉSULTATS DE L'EXTRACTION:")
        logger.info("─" * 50)
        
        # Mandat
        if metadata.get('mandat'):
            mandat = metadata['mandat']
            logger.info(f"✓ Mandat: {mandat.full_reference} (confiance: {mandat.confidence:.2%})")
        else:
            logger.warning("✗ Mandat: NON TROUVÉ")
        
        # Bordereau
        if metadata.get('bordereau'):
            bordereau = metadata['bordereau']
            logger.info(f"✓ Bordereau: {bordereau.full_reference} (confiance: {bordereau.confidence:.2%})")
        else:
            logger.warning("✗ Bordereau: NON TROUVÉ")
        
        # Exercice
        if metadata.get('exercice'):
            logger.info(f"✓ Exercice: {metadata['exercice']}")
        else:
            logger.warning("✗ Exercice: NON TROUVÉ")
        
        # Dates
        dates = metadata.get('dates', [])
        if dates:
            logger.info(f"✓ Dates trouvées: {len(dates)}")
            for date in dates[:3]:  # Afficher max 3 dates
                logger.info(f"  - {date['formatted']} (type: {date['type']})")
        
        # Montants
        amounts = metadata.get('amounts', [])
        if amounts:
            logger.info(f"✓ Montants trouvés: {len(amounts)}")
            for amount in amounts[:3]:
                logger.info(f"  - {amount['formatted']} (type: {amount['type']})")
        
        # Bénéficiaire
        if metadata.get('beneficiaire'):
            beneficiaire = metadata['beneficiaire']
            logger.info(f"✓ Bénéficiaire: {beneficiaire['name']}")
        
        # Validation
        logger.info(f"\n🔍 VALIDATION:")
        logger.info(f"  Valid: {validation['is_valid']}")
        logger.info(f"  Confiance globale: {validation['confidence']:.2%}")
        
        if validation['errors']:
            logger.error("  ❌ Erreurs:")
            for error in validation['errors']:
                logger.error(f"    - {error}")
        
        if validation['warnings']:
            logger.warning("  ⚠️  Avertissements:")
            for warning in validation['warnings']:
                logger.warning(f"    - {warning}")
    
    def _compare_with_ground_truth(self, metadata: Dict, expected: Dict) -> Dict:
        """Compare les résultats avec les données attendues"""
        comparison = {
            'matches': {},
            'mismatches': {},
            'missing': {},
            'accuracy': 0.0
        }
        
        total_fields = 0
        correct_fields = 0
        
        # Comparer mandat
        if 'mandat' in expected:
            total_fields += 1
            extracted = metadata.get('mandat')
            
            if extracted and extracted.number == expected['mandat']:
                comparison['matches']['mandat'] = True
                correct_fields += 1
            elif extracted:
                comparison['mismatches']['mandat'] = {
                    'expected': expected['mandat'],
                    'got': extracted.number
                }
            else:
                comparison['missing']['mandat'] = expected['mandat']
        
        # Comparer bordereau
        if 'bordereau' in expected:
            total_fields += 1
            extracted = metadata.get('bordereau')
            
            if extracted and extracted.number == expected['bordereau']:
                comparison['matches']['bordereau'] = True
                correct_fields += 1
            elif extracted:
                comparison['mismatches']['bordereau'] = {
                    'expected': expected['bordereau'],
                    'got': extracted.number
                }
            else:
                comparison['missing']['bordereau'] = expected['bordereau']
        
        # Comparer exercice
        if 'exercice' in expected:
            total_fields += 1
            extracted = metadata.get('exercice')
            
            if extracted == expected['exercice']:
                comparison['matches']['exercice'] = True
                correct_fields += 1
            elif extracted:
                comparison['mismatches']['exercice'] = {
                    'expected': expected['exercice'],
                    'got': extracted
                }
            else:
                comparison['missing']['exercice'] = expected['exercice']
        
        # Calculer l'accuracy
        if total_fields > 0:
            comparison['accuracy'] = correct_fields / total_fields
        
        return comparison
    
    def _display_comparison(self, comparison: Dict):
        """Affiche la comparaison avec le ground truth"""
        logger.info(f"\n🎯 COMPARAISON AVEC GROUND TRUTH:")
        logger.info("─" * 50)
        
        accuracy = comparison['accuracy']
        logger.info(f"Précision: {accuracy:.1%}")
        
        if comparison['matches']:
            logger.info("✅ Correspondances:")
            for field in comparison['matches']:
                logger.info(f"  - {field}")
        
        if comparison['mismatches']:
            logger.error("❌ Erreurs:")
            for field, values in comparison['mismatches'].items():
                logger.error(f"  - {field}: attendu '{values['expected']}', obtenu '{values['got']}'")
        
        if comparison['missing']:
            logger.warning("⚠️  Champs manquants:")
            for field, expected_value in comparison['missing'].items():
                logger.warning(f"  - {field}: attendu '{expected_value}'")
    
    def _serialize_metadata(self, metadata: Dict) -> Dict:
        """Sérialise les métadonnées pour JSON"""
        serialized = {}
        
        for key, value in metadata.items():
            if value is None:
                serialized[key] = None
            elif hasattr(value, 'dict'):
                serialized[key] = value.dict()
            elif isinstance(value, list):
                serialized[key] = [
                    item.dict() if hasattr(item, 'dict') else item
                    for item in value
                ]
            else:
                serialized[key] = value
        
        return serialized
    
    def generate_report(self, output_file: Optional[Path] = None):
        """Génère un rapport de test"""
        if not self.results:
            logger.warning("Aucun résultat à rapporter")
            return
        
        logger.info(f"\n{'='*70}")
        logger.info("📊 RAPPORT GLOBAL")
        logger.info(f"{'='*70}")
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - successful_tests
        
        # Statistiques globales
        logger.info(f"\nTests exécutés: {total_tests}")
        logger.info(f"  ✅ Réussis: {successful_tests} ({successful_tests/total_tests:.1%})")
        logger.info(f"  ❌ Échoués: {failed_tests}")
        
        # Temps moyen
        processing_times = [r['processing_time'] for r in self.results if 'processing_time' in r]
        if processing_times:
            avg_time = sum(processing_times) / len(processing_times)
            logger.info(f"\nTemps moyen: {avg_time:.2f}s")
        
        # Précision moyenne (si comparaison disponible)
        accuracies = [
            r['comparison']['accuracy']
            for r in self.results
            if r.get('comparison') and 'accuracy' in r['comparison']
        ]
        
        if accuracies:
            avg_accuracy = sum(accuracies) / len(accuracies)
            logger.info(f"Précision moyenne: {avg_accuracy:.1%}")
        
        # Sauvegarde JSON
        if output_file:
            output_file = Path(output_file)
        else:
            output_file = Path(f"ocr_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'successful_tests': successful_tests,
                    'failed_tests': failed_tests,
                    'average_processing_time': avg_time if processing_times else None,
                    'average_accuracy': avg_accuracy if accuracies else None,
                    'timestamp': datetime.now().isoformat()
                },
                'results': self.results
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✅ Rapport sauvegardé: {output_file}")


# =================================================================
# FONCTION PRINCIPALE
# =================================================================

async def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(
        description="Script de test pour l'extraction OCR sur mandats FEICOM"
    )
    
    parser.add_argument(
        '--file',
        type=Path,
        help="Fichier unique à tester"
    )
    
    parser.add_argument(
        '--directory',
        type=Path,
        help="Répertoire contenant les fichiers à tester"
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help="Tester tous les fichiers dans ./test_documents/"
    )
    
    parser.add_argument(
        '--engine',
        type=str,
        default='auto',
        choices=['auto', 'paddleocr', 'easyocr', 'kraken'],
        help="Moteur OCR à utiliser"
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        help="Fichier de sortie pour le rapport JSON"
    )
    
    args = parser.parse_args()
    
    # Validation des arguments
    if not any([args.file, args.directory, args.all]):
        parser.error("Vous devez spécifier --file, --directory ou --all")
    
    try:
        # Initialisation
        tester = OCRTester()
        await tester.initialize()
        
        # Exécution des tests
        if args.file:
            if not args.file.exists():
                logger.error(f"Fichier introuvable: {args.file}")
                return 1
            
            expected = GROUND_TRUTH.get(args.file.name)
            await tester.test_single_file(args.file, args.engine, expected)
        
        elif args.directory:
            if not args.directory.is_dir():
                logger.error(f"Répertoire introuvable: {args.directory}")
                return 1
            
            await tester.test_directory(args.directory, args.engine)
        
        elif args.all:
            test_dir = Path('./test_documents')
            if not test_dir.exists():
                logger.warning(f"Création du répertoire {test_dir}")
                test_dir.mkdir(parents=True)
            
            await tester.test_directory(test_dir, args.engine)
        
        # Génération du rapport
        tester.generate_report(args.output)
        
        return 0
        
    except Exception as e:
        logger.error(f"Erreur fatale: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))