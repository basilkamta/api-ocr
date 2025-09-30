# Architecture API OCR Multi-Moteurs (PaddleOCR, Kraken, EasyOCR)

## 📁 Structure Complète de l'Application

```
ocr-api-v2/
│
├── app/
│   ├── __init__.py
│   ├── main.py                          # Point d'entrée FastAPI
│   ├── config.py                        # Configuration globale
│   ├── dependencies.py                  # Dépendances FastAPI
│   ├── exceptions.py                    # Exceptions personnalisées
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py                  # Authentification, JWT, API Keys
│   │   ├── logging.py                   # Configuration logs structurés
│   │   ├── metrics.py                   # Métriques Prometheus
│   │   └── middleware.py                # Middlewares personnalisés
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                      # Dépendances API
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py                   # Agrégateur de routes
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── health.py            # Santé et monitoring
│   │           ├── ocr.py               # Extraction OCR
│   │           ├── engines.py           # Gestion des moteurs
│   │           ├── documents.py         # Gestion documents
│   │           ├── batch.py             # Traitement par lots
│   │           ├── validation.py        # Validation données
│   │           └── admin.py             # Administration
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                      # Modèles de base
│   │   ├── ocr.py                       # Modèles OCR (Request/Response)
│   │   ├── document.py                  # Modèles documents
│   │   ├── engine.py                    # Modèles moteurs OCR
│   │   ├── validation.py                # Modèles validation
│   │   └── batch.py                     # Modèles traitement batch
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── ocr.py                       # Schémas Pydantic OCR
│   │   ├── document.py                  # Schémas documents
│   │   ├── engine.py                    # Schémas moteurs
│   │   ├── user.py                      # Schémas utilisateurs
│   │   └── responses.py                 # Schémas réponses communes
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── base_ocr.py                  # Service OCR abstrait
│   │   ├── paddleocr_service.py         # Service PaddleOCR
│   │   ├── kraken_service.py            # Service Kraken
│   │   ├── easyocr_service.py           # Service EasyOCR
│   │   ├── ocr_factory.py               # Factory pour moteurs
│   │   ├── preprocessing.py             # Preprocessing images
│   │   ├── postprocessing.py            # Postprocessing résultats
│   │   ├── validation_service.py        # Validation métadonnées
│   │   ├── document_service.py          # Gestion documents
│   │   ├── batch_service.py             # Traitement batch
│   │   └── cache_service.py             # Service de cache
│   │
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── base_extractor.py            # Extracteur abstrait
│   │   ├── mandat_extractor.py          # Extraction mandats
│   │   ├── bordereau_extractor.py       # Extraction bordereaux
│   │   ├── exercice_extractor.py        # Extraction exercices
│   │   ├── date_extractor.py            # Extraction dates
│   │   └── amount_extractor.py          # Extraction montants
│   │
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── base_validator.py            # Validateur abstrait
│   │   ├── mandat_validator.py          # Validation mandats
│   │   ├── bordereau_validator.py       # Validation bordereaux
│   │   ├── format_validator.py          # Validation formats
│   │   └── business_validator.py        # Règles métier
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_utils.py                # Utilitaires fichiers
│   │   ├── image_utils.py               # Utilitaires images
│   │   ├── text_utils.py                # Utilitaires texte
│   │   ├── pattern_utils.py             # Patterns regex
│   │   ├── date_utils.py                # Utilitaires dates
│   │   └── helpers.py                   # Helpers génériques
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                      # Base SQLAlchemy
│   │   ├── session.py                   # Sessions DB
│   │   ├── models.py                    # Modèles DB
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── document_repo.py         # Repository documents
│   │       ├── ocr_result_repo.py       # Repository résultats OCR
│   │       └── user_repo.py             # Repository utilisateurs
│   │
│   └── tasks/
│       ├── __init__.py
│       ├── celery_app.py                # Configuration Celery
│       ├── ocr_tasks.py                 # Tâches OCR asynchrones
│       └── cleanup_tasks.py             # Tâches de nettoyage
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                      # Configuration pytest
│   ├── unit/
│   │   ├── test_services/
│   │   ├── test_extractors/
│   │   └── test_validators/
│   ├── integration/
│   │   ├── test_api/
│   │   └── test_db/
│   └── e2e/
│       └── test_full_flow.py
│
├── alembic/                             # Migrations DB
│   ├── versions/
│   └── env.py
│
├── scripts/
│   ├── download_models.py               # Téléchargement modèles IA
│   ├── setup_db.py                      # Configuration DB
│   ├── seed_data.py                     # Données de test
│   └── benchmark.py                     # Benchmarks performance
│
├── deployment/
│   ├── docker/
│   │   ├── Dockerfile.base              # Image de base
│   │   ├── Dockerfile.api               # Image API
│   │   ├── Dockerfile.worker            # Image worker Celery
│   │   └── docker-compose.yml           # Composition complète
│   ├── kubernetes/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── ingress.yaml
│   └── nginx/
│       └── nginx.conf                   # Configuration Nginx
│
├── docs/
│   ├── architecture.md
│   ├── api_reference.md
│   ├── deployment.md
│   └── development.md
│
├── .env.example                         # Variables d'environnement
├── .gitignore
├── requirements/
│   ├── base.txt                         # Dépendances de base
│   ├── paddle.txt                       # Dépendances PaddleOCR
│   ├── kraken.txt                       # Dépendances Kraken
│   ├── easy.txt                         # Dépendances EasyOCR
│   ├── dev.txt                          # Dépendances développement
│   └── prod.txt                         # Dépendances production
├── requirements.txt                     # Toutes les dépendances
├── pyproject.toml                       # Configuration projet
├── README.md
└── Makefile                            # Commandes de gestion
```

## 📦 Dépendances Complètes

### requirements/base.txt
```
# Framework Web
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-multipart==0.0.6

# Base de données
sqlalchemy==2.0.25
alembic==1.13.1
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Cache et Message Queue
redis==5.0.1
celery==5.3.6
kombu==5.3.5

# Sécurité
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Monitoring et Logs
prometheus-client==0.19.0
structlog==24.1.0
python-json-logger==2.0.7

# Utilitaires
aiofiles==23.2.1
python-dateutil==2.8.2
pytz==2024.1
```

### requirements/paddle.txt
```
# PaddleOCR
paddlepaddle==2.6.0
paddleocr==2.7.3
shapely==2.0.2
scikit-image==0.22.0
```

### requirements/kraken.txt
```
# Kraken OCR
kraken==4.3.13
lxml==5.1.0
Click==8.1.7
```

### requirements/easy.txt
```
# EasyOCR
easyocr==1.7.1
torch==2.1.2
torchvision==0.16.2
```

### requirements/common.txt (traitement d'images)
```
# Traitement d'images et PDF
opencv-python-headless==4.9.0.80
Pillow==10.2.0
PyMuPDF==1.23.21
pdf2image==1.17.0
numpy==1.26.3
scipy==1.12.0

# OCR traditionnel (fallback)
pytesseract==0.3.10
```

### requirements/dev.txt
```
# Tests
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
pytest-mock==3.12.0
httpx==0.26.0

# Qualité de code
black==24.1.1
flake8==7.0.0
mypy==1.8.0
isort==5.13.2
pylint==3.0.3

# Documentation
mkdocs==1.5.3
mkdocs-material==9.5.6
```

## 🛣️ Routes API Exhaustives

### 1. Routes Santé et Monitoring
```
GET    /                                 # Page d'accueil API
GET    /health                           # Santé globale
GET    /health/detailed                  # Santé détaillée (tous services)
GET    /health/live                      # Liveness probe (K8s)
GET    /health/ready                     # Readiness probe (K8s)
GET    /metrics                          # Métriques Prometheus
GET    /version                          # Version de l'API
```

### 2. Routes OCR Principales
```
POST   /api/v1/ocr/extract               # Extraction simple (1 fichier)
POST   /api/v1/ocr/extract/advanced      # Extraction avancée (options complètes)
POST   /api/v1/ocr/batch                 # Extraction batch (plusieurs fichiers)
GET    /api/v1/ocr/batch/{batch_id}      # Statut traitement batch
GET    /api/v1/ocr/result/{result_id}    # Récupérer un résultat
DELETE /api/v1/ocr/result/{result_id}    # Supprimer un résultat
GET    /api/v1/ocr/results               # Liste des résultats (paginée)
POST   /api/v1/ocr/reprocess/{result_id} # Retraiter un document
```

### 3. Routes Moteurs OCR
```
GET    /api/v1/engines                   # Liste tous les moteurs
GET    /api/v1/engines/{engine_name}     # Détails d'un moteur
GET    /api/v1/engines/{engine_name}/status # Statut d'un moteur
POST   /api/v1/engines/{engine_name}/test    # Tester un moteur
GET    /api/v1/engines/compare           # Comparer les moteurs
POST   /api/v1/engines/benchmark         # Benchmark moteurs
```

### 4. Routes Documents
```
GET    /api/v1/documents                 # Liste documents (paginée, filtres)
GET    /api/v1/documents/{doc_id}        # Détails d'un document
POST   /api/v1/documents/upload          # Upload document
DELETE /api/v1/documents/{doc_id}        # Supprimer document
GET    /api/v1/documents/{doc_id}/preview # Aperçu document
GET    /api/v1/documents/{doc_id}/download # Télécharger document
PATCH  /api/v1/documents/{doc_id}        # Mettre à jour métadonnées
GET    /api/v1/documents/search          # Recherche documents
GET    /api/v1/documents/stats           # Statistiques documents
```

### 5. Routes Validation
```
POST   /api/v1/validation/validate       # Valider des métadonnées
POST   /api/v1/validation/mandat         # Valider un mandat
POST   /api/v1/validation/bordereau      # Valider un bordereau
POST   /api/v1/validation/hierarchy      # Valider hiérarchie mandat-bordereau
GET    /api/v1/validation/rules          # Liste règles de validation
POST   /api/v1/validation/custom-rule    # Ajouter règle personnalisée
```

### 6. Routes Extraction Spécialisées
```
POST   /api/v1/extract/mandat            # Extraire seulement mandat
POST   /api/v1/extract/bordereau         # Extraire seulement bordereau
POST   /api/v1/extract/exercice          # Extraire seulement exercice
POST   /api/v1/extract/dates             # Extraire toutes les dates
POST   /api/v1/extract/amounts           # Extraire tous les montants
POST   /api/v1/extract/signatures        # Détecter signatures
POST   /api/v1/extract/tables            # Extraire tableaux
POST   /api/v1/extract/zones             # Extraction par zones
```

### 7. Routes Traitement Batch
```
POST   /api/v1/batch/create              # Créer batch
GET    /api/v1/batch/list                # Liste des batchs
GET    /api/v1/batch/{batch_id}          # Détails batch
GET    /api/v1/batch/{batch_id}/status   # Statut batch
POST   /api/v1/batch/{batch_id}/cancel   # Annuler batch
GET    /api/v1/batch/{batch_id}/results  # Résultats batch
POST   /api/v1/batch/{batch_id}/retry    # Réessayer batch
DELETE /api/v1/batch/{batch_id}          # Supprimer batch
GET    /api/v1/batch/{batch_id}/export   # Exporter résultats (CSV/JSON)
```

### 8. Routes Cache
```
GET    /api/v1/cache/stats               # Statistiques cache
DELETE /api/v1/cache/clear                # Vider cache
DELETE /api/v1/cache/{key}                # Supprimer une clé
GET    /api/v1/cache/keys                # Liste des clés
```

### 9. Routes Configuration
```
GET    /api/v1/config                    # Configuration actuelle
PATCH  /api/v1/config                    # Mettre à jour config
GET    /api/v1/config/engines            # Config moteurs OCR
PATCH  /api/v1/config/engines/{engine}   # Config moteur spécifique
GET    /api/v1/config/preprocessing      # Config preprocessing
PATCH  /api/v1/config/preprocessing      # Modifier preprocessing
```

### 10. Routes Administration
```
GET    /api/v1/admin/users               # Liste utilisateurs
POST   /api/v1/admin/users               # Créer utilisateur
GET    /api/v1/admin/users/{user_id}     # Détails utilisateur
PATCH  /api/v1/admin/users/{user_id}     # Modifier utilisateur
DELETE /api/v1/admin/users/{user_id}     # Supprimer utilisateur
GET    /api/v1/admin/api-keys            # Liste API keys
POST   /api/v1/admin/api-keys            # Générer API key
DELETE /api/v1/admin/api-keys/{key_id}   # Révoquer API key
GET    /api/v1/admin/logs                # Logs système
GET    /api/v1/admin/stats               # Statistiques globales
POST   /api/v1/admin/cleanup             # Nettoyage base de données
```

### 11. Routes Webhooks
```
GET    /api/v1/webhooks                  # Liste webhooks
POST   /api/v1/webhooks                  # Créer webhook
GET    /api/v1/webhooks/{webhook_id}     # Détails webhook
PATCH  /api/v1/webhooks/{webhook_id}     # Modifier webhook
DELETE /api/v1/webhooks/{webhook_id}     # Supprimer webhook
POST   /api/v1/webhooks/{webhook_id}/test # Tester webhook
```

### 12. Routes Export/Import
```
POST   /api/v1/export/results            # Exporter résultats (CSV/JSON/Excel)
POST   /api/v1/export/documents          # Exporter documents
POST   /api/v1/import/documents          # Importer documents en masse
GET    /api/v1/export/templates          # Templates d'export disponibles
```

### 13. Routes Rapports
```
GET    /api/v1/reports/daily             # Rapport journalier
GET    /api/v1/reports/weekly            # Rapport hebdomadaire
GET    /api/v1/reports/monthly           # Rapport mensuel
GET    /api/v1/reports/performance       # Rapport performance
GET    /api/v1/reports/errors            # Rapport erreurs
POST   /api/v1/reports/custom            # Rapport personnalisé
```

### 14. Routes Authentification
```
POST   /api/v1/auth/login                # Connexion
POST   /api/v1/auth/logout               # Déconnexion
POST   /api/v1/auth/refresh              # Rafraîchir token
POST   /api/v1/auth/register             # Enregistrement
POST   /api/v1/auth/password/reset       # Réinitialiser mot de passe
POST   /api/v1/auth/password/change      # Changer mot de passe
GET    /api/v1/auth/me                   # Profil utilisateur
```

## 🔑 Paramètres d'Extraction OCR Complets

### POST /api/v1/ocr/extract/advanced

**Body Parameters:**
```json
{
  "engine": "paddleocr|kraken|easyocr|auto",
  "engines_fallback": ["paddleocr", "easyocr"],
  "extraction_mode": "standard|fast|accurate|hybrid",
  
  "extract": {
    "mandat": true,
    "bordereau": true,
    "exercice": true,
    "dates": true,
    "amounts": true,
    "beneficiaire": true,
    "signatures": false,
    "tables": false,
    "all_text": false
  },
  
  "preprocessing": {
    "deskew": true,
    "denoise": true,
    "enhance_contrast": true,
    "binarize": true,
    "remove_borders": true,
    "upscale": false,
    "target_dpi": 400
  },
  
  "ocr_options": {
    "languages": ["fra", "eng"],
    "detect_orientation": true,
    "detect_tables": true,
    "confidence_threshold": 0.7,
    "use_gpu": true
  },
  
  "zones": {
    "header": {"x": 0.6, "y": 0, "width": 0.4, "height": 0.3},
    "custom_zones": []
  },
  
  "validation": {
    "validate_format": true,
    "validate_business_rules": true,
    "check_erp": false,
    "strict_mode": false
  },
  
  "output": {
    "include_raw_text": true,
    "include_coordinates": true,
    "include_confidence_scores": true,
    "include_debug_images": false,
    "format": "json"
  },
  
  "cache": {
    "use_cache": true,
    "cache_ttl": 3600
  },
  
  "callback": {
    "webhook_url": "https://your-server.com/webhook",
    "on_completion": true,
    "on_error": true
  }
}
```

## 📊 Modèles de Réponse Complets

### OCRExtractionResponse
```json
{
  "id": "uuid",
  "success": true,
  "processing_time": 2.45,
  "timestamp": "2025-01-15T10:30:00Z",
  
  "document": {
    "id": "doc_uuid",
    "filename": "MD_2412034.pdf",
    "file_size": 245678,
    "mime_type": "application/pdf",
    "pages": 1,
    "hash": "sha256_hash"
  },
  
  "engine": {
    "primary": "paddleocr",
    "fallbacks_used": [],
    "version": "2.7.3"
  },
  
  "extracted_data": {
    "mandat": {
      "type": "mandat",
      "number": "2412034",
      "full_reference": "MD/2412034",
      "confidence": 0.95,
      "coordinates": {"x": 650, "y": 80, "width": 150, "height": 30},
      "raw_text": "MD/2412034"
    },
    "bordereau": {
      "type": "bordereau",
      "number": "2402756",
      "full_reference": "BOR/2402756",
      "confidence": 0.92,
      "coordinates": {"x": 650, "y": 45, "width": 150, "height": 30},
      "raw_text": "BOR/2402756"
    },
    "exercice": {
      "value": "2024",
      "confidence": 0.98,
      "coordinates": {"x": 650, "y": 10, "width": 80, "height": 25}
    },
    "dates": [
      {
        "type": "emission",
        "value": "2024-12-15",
        "formatted": "15/12/2024",
        "confidence": 0.89
      }
    ],
    "amounts": [
      {
        "type": "total",
        "value": 5672860.00,
        "currency": "XAF",
        "formatted": "5 672 860 FCFA",
        "confidence": 0.94
      }
    ]
  },
  
  "validation": {
    "is_valid": true,
    "confidence_score": 0.93,
    "issues": [],
    "warnings": ["Bordereau non vérifié dans l'ERP"],
    "hierarchy_valid": true
  },
  
  "raw_text": "Texte brut complet extrait...",
  
  "metadata": {
    "preprocessing_applied": ["deskew", "denoise", "enhance_contrast"],
    "zones_processed": ["header", "body"],
    "total_characters": 1234,
    "detected_language": "fra"
  },
  
  "quality_metrics": {
    "image_quality": 0.85,
    "text_clarity": 0.90,
    "overall_score": 0.88
  }
}
```

Ce plan d'architecture est complet et prêt pour l'implémentation. Voulez-vous que je commence par implémenter une partie spécifique (services OCR, routes, modèles) ?