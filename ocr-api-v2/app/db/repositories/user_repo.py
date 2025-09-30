from sqlalchemy.orm import Session
from typing import List, Optional

from ...models.user import User, APIKey
from ...schemas.user import UserRole

class UserRepository:
    """Repository pour les utilisateurs"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, **kwargs) -> User:
        """Crée un utilisateur"""
        user = User(**kwargs)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Récupère par ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Récupère par username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Récupère par email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Liste les utilisateurs"""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def update(self, user_id: str, **kwargs) -> Optional[User]:
        """Met à jour un utilisateur"""
        user = self.get_by_id(user_id)
        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def delete(self, user_id: str) -> bool:
        """Supprime un utilisateur"""
        user = self.get_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False

class APIKeyRepository:
    """Repository pour les clés API"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, **kwargs) -> APIKey:
        """Crée une clé API"""
        api_key = APIKey(**kwargs)
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        return api_key
    
    def get_by_key(self, key: str) -> Optional[APIKey]:
        """Récupère par clé"""
        return self.db.query(APIKey).filter(
            APIKey.key == key,
            APIKey.is_active == True
        ).first()
    
    def list_keys(self, user_id: Optional[str] = None) -> List[APIKey]:
        """Liste les clés"""
        query = self.db.query(APIKey)
        # if user_id:
        #     query = query.filter(APIKey.user_id == user_id)
        return query.all()
    
    def revoke(self, key_id: str) -> bool:
        """Révoque une clé"""
        api_key = self.db.query(APIKey).filter(APIKey.id == key_id).first()
        if api_key:
            api_key.is_active = False
            self.db.commit()
            return True
        return False
