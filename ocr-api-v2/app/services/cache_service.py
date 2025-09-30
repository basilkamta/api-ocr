"""
Service de cache (Redis ou in-memory)
"""
import logging
import json
import hashlib
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheService:
    """
    Service de cache avec support Redis ou fallback in-memory
    
    Fonctionnalités:
    - Cache des résultats OCR
    - Cache des documents traités
    - TTL (Time To Live) configurable
    - Invalidation de cache
    """
    
    def __init__(self):
        self.redis_client: Optional[Any] = None
        self.memory_cache: Dict[str, Dict] = {}  # Fallback in-memory
        self.use_redis = False
        
        # Tentative de connexion Redis
        if REDIS_AVAILABLE and settings.redis_url:
            try:
                self.redis_client = redis.from_url(
                    settings.redis_url,
                    decode_responses=True
                )
                # Test de connexion
                self.redis_client.ping()
                self.use_redis = True
                logger.info("✅ Cache Redis activé")
            except Exception as e:
                logger.warning(f"Redis non disponible, utilisation cache mémoire: {e}")
                self.use_redis = False
        else:
            logger.info("Cache in-memory activé (Redis non configuré)")
    
    def _generate_cache_key(self, prefix: str, identifier: str) -> str:
        """
        Génère une clé de cache unique
        
        Args:
            prefix: Préfixe (ocr_result, document, etc.)
            identifier: Identifiant (hash fichier, doc_id, etc.)
        
        Returns:
            Clé de cache
        """
        return f"{prefix}:{identifier}"
    
    def _hash_content(self, content: bytes) -> str:
        """Génère un hash SHA256 du contenu"""
        return hashlib.sha256(content).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur du cache
        
        Args:
            key: Clé de cache
        
        Returns:
            Valeur ou None si pas trouvée/expirée
        """
        try:
            if self.use_redis and self.redis_client:
                # Redis
                value = self.redis_client.get(key)
                if value:
                    logger.debug(f"Cache HIT (Redis): {key}")
                    return json.loads(value)
                else:
                    logger.debug(f"Cache MISS (Redis): {key}")
                    return None
            else:
                # In-memory
                cache_entry = self.memory_cache.get(key)
                
                if cache_entry:
                    # Vérifier expiration
                    if 'expires_at' in cache_entry:
                        if datetime.utcnow() > datetime.fromisoformat(cache_entry['expires_at']):
                            # Expiré, supprimer
                            del self.memory_cache[key]
                            logger.debug(f"Cache EXPIRED (Memory): {key}")
                            return None
                    
                    logger.debug(f"Cache HIT (Memory): {key}")
                    return cache_entry['value']
                else:
                    logger.debug(f"Cache MISS (Memory): {key}")
                    return None
                    
        except Exception as e:
            logger.error(f"Erreur récupération cache {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Stocke une valeur dans le cache
        
        Args:
            key: Clé de cache
            value: Valeur à stocker
            ttl: Time to live en secondes (défaut: settings.cache_ttl)
        
        Returns:
            True si succès
        """
        try:
            ttl = ttl or settings.cache_ttl
            
            if self.use_redis and self.redis_client:
                # Redis
                self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value, default=str)
                )
                logger.debug(f"Cache SET (Redis): {key} (TTL: {ttl}s)")
                return True
            else:
                # In-memory
                expires_at = datetime.utcnow() + timedelta(seconds=ttl)
                self.memory_cache[key] = {
                    'value': value,
                    'expires_at': expires_at.isoformat()
                }
                logger.debug(f"Cache SET (Memory): {key} (TTL: {ttl}s)")
                return True
                
        except Exception as e:
            logger.error(f"Erreur stockage cache {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Supprime une clé du cache
        
        Args:
            key: Clé à supprimer
        
        Returns:
            True si supprimé
        """
        try:
            if self.use_redis and self.redis_client:
                deleted = self.redis_client.delete(key)
                logger.debug(f"Cache DELETE (Redis): {key}")
                return bool(deleted)
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    logger.debug(f"Cache DELETE (Memory): {key}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Erreur suppression cache {key}: {e}")
            return False
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        """
        Vide le cache (tout ou par pattern)
        
        Args:
            pattern: Pattern de clés à supprimer (ex: "ocr_result:*")
        
        Returns:
            Nombre de clés supprimées
        """
        try:
            if self.use_redis and self.redis_client:
                if pattern:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        deleted = self.redis_client.delete(*keys)
                        logger.info(f"Cache CLEAR (Redis): {deleted} clé(s) supprimée(s)")
                        return deleted
                else:
                    self.redis_client.flushdb()
                    logger.info("Cache CLEAR (Redis): Tout supprimé")
                    return -1  # Inconnu
            else:
                if pattern:
                    # Filtrer par pattern
                    import fnmatch
                    keys_to_delete = [
                        k for k in self.memory_cache.keys()
                        if fnmatch.fnmatch(k, pattern)
                    ]
                    for key in keys_to_delete:
                        del self.memory_cache[key]
                    logger.info(f"Cache CLEAR (Memory): {len(keys_to_delete)} clé(s)")
                    return len(keys_to_delete)
                else:
                    count = len(self.memory_cache)
                    self.memory_cache.clear()
                    logger.info(f"Cache CLEAR (Memory): {count} clé(s)")
                    return count
                    
        except Exception as e:
            logger.error(f"Erreur vidage cache: {e}")
            return 0
    
    async def cache_ocr_result(
        self,
        file_hash: str,
        ocr_result: Dict,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache un résultat OCR
        
        Args:
            file_hash: Hash du fichier
            ocr_result: Résultat OCR à cacher
            ttl: Durée de vie en secondes
        
        Returns:
            True si succès
        """
        key = self._generate_cache_key("ocr_result", file_hash)
        return await self.set(key, ocr_result, ttl)
    
    async def get_cached_ocr_result(self, file_hash: str) -> Optional[Dict]:
        """
        Récupère un résultat OCR depuis le cache
        
        Args:
            file_hash: Hash du fichier
        
        Returns:
            Résultat OCR ou None
        """
        key = self._generate_cache_key("ocr_result", file_hash)
        return await self.get(key)
    
    async def get_statistics(self) -> Dict:
        """
        Retourne des statistiques sur le cache
        
        Returns:
            Dict avec stats
        """
        try:
            if self.use_redis and self.redis_client:
                info = self.redis_client.info('stats')
                return {
                    'type': 'redis',
                    'connected': True,
                    'total_keys': self.redis_client.dbsize(),
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0)
                }
            else:
                return {
                    'type': 'memory',
                    'connected': True,
                    'total_keys': len(self.memory_cache),
                    'hits': 'N/A',
                    'misses': 'N/A'
                }
        except Exception as e:
            logger.error(f"Erreur récupération stats cache: {e}")
            return {
                'type': 'unknown',
                'connected': False,
                'error': str(e)
            }


# =================================================================
# Instance globale (Singleton)
# =================================================================

_cache_service_instance: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Récupère l'instance du service cache (Singleton)"""
    global _cache_service_instance
    
    if _cache_service_instance is None:
        _cache_service_instance = CacheService()
    
    return _cache_service_instance