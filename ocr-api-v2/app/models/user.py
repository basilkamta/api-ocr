from sqlalchemy import Column, String, Boolean, Enum as SQLEnum, DateTime
from .base import TimeStampedModel
from ..schemas.user import UserRole
import uuid

class User(TimeStampedModel):
    """Utilisateur de l'API"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)

class APIKey(TimeStampedModel):
    """Clé API"""
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    last_used = Column(DateTime)
    
    # Relations
    # user_id = Column(String, ForeignKey('users.id'))