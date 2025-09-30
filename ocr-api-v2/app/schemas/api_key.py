from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class APIKeyCreate(BaseModel):
    """Création de clé API"""
    name: str
    description: Optional[str] = None
    expires_at: Optional[datetime] = None

class APIKeyResponse(BaseModel):
    """Réponse clé API"""
    id: str
    name: str
    key: str  # Visible seulement à la création
    description: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool

class APIKeyListResponse(BaseModel):
    """Liste de clés API"""
    api_keys: List[APIKeyResponse]
    total: int