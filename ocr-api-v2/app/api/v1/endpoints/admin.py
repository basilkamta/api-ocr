"""
Endpoints d'administration
"""
from fastapi import APIRouter, Depends, HTTPException, status

from ....dependencies import get_current_api_key
from ....config import get_settings

router = APIRouter()
settings = get_settings()

# Dépendance admin
async def verify_admin_access(api_key: str = Depends(get_current_api_key)):
    """Vérifie que l'utilisateur a les droits admin"""
    # À implémenter avec un système de rôles
    # Pour l'instant, tous les utilisateurs authentifiés sont admin
    return api_key

@router.get("/users", tags=["Admin"])
async def list_users(
    admin: str = Depends(verify_admin_access)
):
    """Liste tous les utilisateurs"""
    # À implémenter avec DB
    return {"users": []}

@router.post("/users", tags=["Admin"])
async def create_user(
    user_data: dict,
    admin: str = Depends(verify_admin_access)
):
    """Crée un nouvel utilisateur"""
    # À implémenter
    return {"message": "User created", "user_id": "user_123"}

@router.get("/users/{user_id}", tags=["Admin"])
async def get_user(
    user_id: str,
    admin: str = Depends(verify_admin_access)
):
    """Détails d'un utilisateur"""
    # À implémenter
    raise HTTPException(404, "User not found")

@router.patch("/users/{user_id}", tags=["Admin"])
async def update_user(
    user_id: str,
    user_data: dict,
    admin: str = Depends(verify_admin_access)
):
    """Met à jour un utilisateur"""
    return {"message": "User updated", "user_id": user_id}

@router.delete("/users/{user_id}", tags=["Admin"])
async def delete_user(
    user_id: str,
    admin: str = Depends(verify_admin_access)
):
    """Supprime un utilisateur"""
    return {"message": "User deleted", "user_id": user_id}

@router.get("/api-keys", tags=["Admin"])
async def list_api_keys(
    admin: str = Depends(verify_admin_access)
):
    """Liste toutes les clés API"""
    # À implémenter
    return {"api_keys": []}

@router.post("/api-keys", tags=["Admin"])
async def generate_api_key(
    key_data: dict,
    admin: str = Depends(verify_admin_access)
):
    """Génère une nouvelle clé API"""
    from ....core.security import generate_api_key
    
    new_key = generate_api_key()
    
    return {
        "api_key": new_key,
        "message": "Clé API générée avec succès"
    }

@router.delete("/api-keys/{key_id}", tags=["Admin"])
async def revoke_api_key(
    key_id: str,
    admin: str = Depends(verify_admin_access)
):
    """Révoque une clé API"""
    return {"message": "API key revoked", "key_id": key_id}

@router.get("/logs", tags=["Admin"])
async def get_logs(
    lines: int = 100,
    level: str = "INFO",
    admin: str = Depends(verify_admin_access)
):
    """Récupère les logs système"""
    # À implémenter avec lecture du fichier de logs
    return {"logs": [], "lines": lines}

@router.get("/stats", tags=["Admin"])
async def get_global_stats(
    admin: str = Depends(verify_admin_access)
):
    """Statistiques globales du système"""
    return {
        "total_requests": 0,
        "total_extractions": 0,
        "success_rate": 0.0,
        "average_processing_time": 0.0,
        "by_engine": {}
    }

@router.post("/cleanup", tags=["Admin"])
async def cleanup_database(
    older_than_days: int = 30,
    admin: str = Depends(verify_admin_access)
):
    """
    Nettoie la base de données
    
    Supprime les résultats plus anciens que N jours
    """
    # À implémenter
    return {
        "message": "Cleanup initiated",
        "older_than_days": older_than_days
    }