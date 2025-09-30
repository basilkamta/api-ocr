"""
Service de gestion des documents
"""
import logging
from pathlib import Path
from typing import Optional, List, Dict, BinaryIO
from datetime import datetime
import hashlib
import shutil

from ..utils.file_utils import (
    get_file_extension,
    get_mime_type,
    calculate_file_hash,
    sanitize_filename,
    generate_unique_filename,
    is_allowed_file,
    get_file_size,
    create_temp_file
)
from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DocumentService:
    """
    Service pour la gestion des documents uploadés
    
    Fonctionnalités:
    - Upload et stockage de documents
    - Génération de métadonnées
    - Gestion du cycle de vie des documents
    - Recherche et récupération
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Args:
            storage_path: Chemin de stockage des documents (défaut: /tmp/uploads)
        """
        self.storage_path = Path(storage_path or settings.upload_dir)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DocumentService initialisé avec storage: {self.storage_path}")
    
    async def save_document(
        self,
        file_content: bytes,
        original_filename: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Sauvegarde un document uploadé
        
        Args:
            file_content: Contenu du fichier (bytes)
            original_filename: Nom original du fichier
            user_id: ID de l'utilisateur (optionnel)
            metadata: Métadonnées additionnelles
        
        Returns:
            Dict avec infos du document sauvegardé
        """
        try:
            # Validation du fichier
            if not is_allowed_file(original_filename):
                raise ValueError(f"Type de fichier non autorisé: {original_filename}")
            
            if len(file_content) > settings.max_file_size:
                raise ValueError(f"Fichier trop volumineux: {len(file_content)} bytes")
            
            # Générer un nom de fichier sécurisé et unique
            safe_filename = sanitize_filename(original_filename)
            unique_filename = generate_unique_filename(safe_filename, self.storage_path)
            
            # Calculer le hash
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Chemin de destination
            file_path = self.storage_path / unique_filename
            
            # Sauvegarder le fichier
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Créer les métadonnées du document
            doc_metadata = {
                'doc_id': file_hash[:16],  # ID unique basé sur le hash
                'filename': unique_filename,
                'original_filename': original_filename,
                'file_path': str(file_path),
                'file_size': len(file_content),
                'file_hash': file_hash,
                'mime_type': get_mime_type(original_filename),
                'extension': get_file_extension(original_filename),
                'uploaded_at': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'status': 'uploaded',
                'metadata': metadata or {}
            }
            
            logger.info(f"Document sauvegardé: {unique_filename} ({len(file_content)} bytes)")
            
            return doc_metadata
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde document: {e}")
            raise
    
    async def get_document(self, doc_id: str) -> Optional[Dict]:
        """
        Récupère les informations d'un document
        
        Args:
            doc_id: ID du document
        
        Returns:
            Métadonnées du document ou None
        """
        # Dans un vrai système, ceci irait chercher dans la DB
        # Pour l'instant, on cherche par hash dans le répertoire
        
        for file_path in self.storage_path.glob("*"):
            if file_path.is_file():
                # Calculer le hash et vérifier
                with open(file_path, 'rb') as f:
                    content = f.read()
                    file_hash = hashlib.sha256(content).hexdigest()
                    
                    if file_hash[:16] == doc_id:
                        return {
                            'doc_id': doc_id,
                            'filename': file_path.name,
                            'file_path': str(file_path),
                            'file_size': len(content),
                            'file_hash': file_hash,
                            'mime_type': get_mime_type(file_path.name)
                        }
        
        return None
    
    async def get_document_content(self, doc_id: str) -> Optional[bytes]:
        """
        Récupère le contenu d'un document
        
        Args:
            doc_id: ID du document
        
        Returns:
            Contenu du fichier (bytes) ou None
        """
        doc_info = await self.get_document(doc_id)
        
        if not doc_info:
            return None
        
        file_path = Path(doc_info['file_path'])
        
        if not file_path.exists():
            logger.error(f"Fichier introuvable: {file_path}")
            return None
        
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Erreur lecture fichier {file_path}: {e}")
            return None
    
    async def delete_document(self, doc_id: str) -> bool:
        """
        Supprime un document
        
        Args:
            doc_id: ID du document
        
        Returns:
            True si supprimé, False sinon
        """
        doc_info = await self.get_document(doc_id)
        
        if not doc_info:
            logger.warning(f"Document non trouvé pour suppression: {doc_id}")
            return False
        
        file_path = Path(doc_info['file_path'])
        
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Document supprimé: {file_path.name}")
                return True
            else:
                logger.warning(f"Fichier déjà supprimé: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Erreur suppression document {doc_id}: {e}")
            return False
    
    async def list_documents(
        self,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict]:
        """
        Liste les documents
        
        Args:
            user_id: Filtrer par utilisateur (optionnel)
            skip: Nombre de documents à sauter (pagination)
            limit: Nombre max de documents à retourner
        
        Returns:
            Liste de métadonnées de documents
        """
        documents = []
        
        for i, file_path in enumerate(self.storage_path.glob("*")):
            if i < skip:
                continue
            
            if len(documents) >= limit:
                break
            
            if file_path.is_file():
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        file_hash = hashlib.sha256(content).hexdigest()
                    
                    documents.append({
                        'doc_id': file_hash[:16],
                        'filename': file_path.name,
                        'file_size': len(content),
                        'mime_type': get_mime_type(file_path.name),
                        'created_at': datetime.fromtimestamp(file_path.stat().st_ctime).isoformat()
                    })
                except Exception as e:
                    logger.error(f"Erreur lecture fichier {file_path}: {e}")
                    continue
        
        return documents
    
    async def search_documents(
        self,
        query: str,
        field: Optional[str] = None
    ) -> List[Dict]:
        """
        Recherche des documents
        
        Args:
            query: Terme de recherche
            field: Champ spécifique à chercher (filename, mime_type, etc.)
        
        Returns:
            Liste de documents correspondants
        """
        all_docs = await self.list_documents(limit=1000)
        
        if not query:
            return all_docs
        
        results = []
        query_lower = query.lower()
        
        for doc in all_docs:
            # Recherche dans le nom de fichier
            if field is None or field == 'filename':
                if query_lower in doc['filename'].lower():
                    results.append(doc)
                    continue
            
            # Recherche dans le type MIME
            if field is None or field == 'mime_type':
                if query_lower in doc.get('mime_type', '').lower():
                    results.append(doc)
                    continue
        
        return results
    
    async def get_statistics(self) -> Dict:
        """
        Retourne des statistiques sur les documents
        
        Returns:
            Dict avec statistiques
        """
        all_docs = await self.list_documents(limit=10000)
        
        total_size = sum(doc['file_size'] for doc in all_docs)
        
        # Compter par type
        by_type = {}
        for doc in all_docs:
            mime_type = doc.get('mime_type', 'unknown')
            by_type[mime_type] = by_type.get(mime_type, 0) + 1
        
        return {
            'total_documents': len(all_docs),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'by_type': by_type,
            'storage_path': str(self.storage_path)
        }
    
    async def cleanup_old_documents(self, days: int = 30) -> int:
        """
        Nettoie les documents anciens
        
        Args:
            days: Supprimer les documents plus vieux que N jours
        
        Returns:
            Nombre de documents supprimés
        """
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = 0
        
        for file_path in self.storage_path.glob("*"):
            if file_path.is_file():
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_mtime < cutoff_date:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Document ancien supprimé: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Erreur suppression {file_path}: {e}")
        
        logger.info(f"Nettoyage terminé: {deleted_count} document(s) supprimé(s)")
        return deleted_count
    
    async def duplicate_check(self, file_content: bytes) -> Optional[str]:
        """
        Vérifie si un document identique existe déjà (par hash)
        
        Args:
            file_content: Contenu du fichier à vérifier
        
        Returns:
            doc_id du document existant ou None
        """
        file_hash = hashlib.sha256(file_content).hexdigest()
        doc_id = file_hash[:16]
        
        existing_doc = await self.get_document(doc_id)
        
        if existing_doc:
            logger.info(f"Document dupliqué détecté: {doc_id}")
            return doc_id
        
        return None


# =================================================================
# Instance globale (Singleton)
# =================================================================

_document_service_instance: Optional[DocumentService] = None


def get_document_service() -> DocumentService:
    """Récupère l'instance du service documents (Singleton)"""
    global _document_service_instance
    
    if _document_service_instance is None:
        _document_service_instance = DocumentService()
    
    return _document_service_instance