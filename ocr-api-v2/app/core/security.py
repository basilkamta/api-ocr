from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader, APIKeyQuery
from typing import Optional
import secrets

from ..config import get_settings

settings = get_settings()

# Schémas de sécurité
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)

async def get_api_key(
    api_key_header_value: Optional[str] = Security(api_key_header),
    api_key_query_value: Optional[str] = Security(api_key_query),
) -> str:
    """
    Valide la clé API depuis le header ou query param
    """
    api_key = api_key_header_value or api_key_query_value
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API manquante",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key

def generate_api_key() -> str:
    """Génère une nouvelle clé API"""
    return secrets.token_urlsafe(32)