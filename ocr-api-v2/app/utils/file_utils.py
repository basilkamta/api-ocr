"""
Utilitaires pour la gestion des fichiers
"""
import os
import hashlib
import mimetypes
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Optional, List, BinaryIO, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# =================================================================
# EXTENSIONS AUTORISÉES
# =================================================================

ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp'}
ALLOWED_DOCUMENT_EXTENSIONS = {'.pdf'}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS

# MIME types correspondants
ALLOWED_MIME_TYPES = {
    'image/png',
    'image/jpeg',
    'image/tiff',
    'image/bmp',
    'image/webp',
    'application/pdf'
}

# =================================================================
# VALIDATION DE FICHIERS
# =================================================================

def is_allowed_file(filename: str) -> bool:
    """
    Vérifie si l'extension du fichier est autorisée
    
    Args:
        filename: Nom du fichier
    
    Returns:
        True si l'extension est autorisée
    """
    if not filename:
        return False
    
    ext = get_file_extension(filename)
    return ext.lower() in ALLOWED_EXTENSIONS


def is_image_file(filename: str) -> bool:
    """
    Vérifie si le fichier est une image
    
    Args:
        filename: Nom du fichier
    
    Returns:
        True si c'est une image
    """
    if not filename:
        return False
    
    ext = get_file_extension(filename)
    return ext.lower() in ALLOWED_IMAGE_EXTENSIONS


def is_pdf_file(filename: str) -> bool:
    """
    Vérifie si le fichier est un PDF
    
    Args:
        filename: Nom du fichier
    
    Returns:
        True si c'est un PDF
    """
    if not filename:
        return False
    
    ext = get_file_extension(filename)
    return ext.lower() == '.pdf'


def validate_mime_type(mime_type: str) -> bool:
    """
    Vérifie si le type MIME est autorisé
    
    Args:
        mime_type: Type MIME du fichier
    
    Returns:
        True si autorisé
    """
    return mime_type in ALLOWED_MIME_TYPES


# =================================================================
# INFORMATIONS SUR LES FICHIERS
# =================================================================

def get_file_extension(filename: str) -> str:
    """
    Récupère l'extension d'un fichier (avec le point)
    
    Args:
        filename: Nom du fichier
    
    Returns:
        Extension (ex: '.pdf', '.png')
    """
    if not filename:
        return ""
    
    return Path(filename).suffix.lower()


def get_filename_without_extension(filename: str) -> str:
    """
    Récupère le nom du fichier sans extension
    
    Args:
        filename: Nom du fichier
    
    Returns:
        Nom sans extension
    """
    if not filename:
        return ""
    
    return Path(filename).stem


def get_mime_type(filename: str) -> str:
    """
    Détermine le type MIME d'un fichier
    
    Args:
        filename: Nom du fichier
    
    Returns:
        Type MIME (ex: 'application/pdf', 'image/png')
    """
    if not filename:
        return "application/octet-stream"
    
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Récupère la taille d'un fichier en octets
    
    Args:
        file_path: Chemin vers le fichier
    
    Returns:
        Taille en octets
    """
    try:
        return Path(file_path).stat().st_size
    except Exception as e:
        logger.error(f"Erreur récupération taille fichier {file_path}: {e}")
        return 0


def format_file_size(size_bytes: int) -> str:
    """
    Formate une taille de fichier en unité lisible
    
    Args:
        size_bytes: Taille en octets
    
    Returns:
        Taille formatée (ex: '1.5 MB', '256 KB')
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.2f} PB"


# =================================================================
# HASH ET EMPREINTES
# =================================================================

def calculate_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Calcule le hash d'un fichier
    
    Args:
        file_path: Chemin vers le fichier
        algorithm: Algorithme de hash ('md5', 'sha1', 'sha256', 'sha512')
    
    Returns:
        Hash hexadécimal
    """
    hash_func = getattr(hashlib, algorithm)()
    
    try:
        with open(file_path, 'rb') as f:
            # Lecture par chunks pour les gros fichiers
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    except Exception as e:
        logger.error(f"Erreur calcul hash {file_path}: {e}")
        return ""


def calculate_content_hash(content: bytes, algorithm: str = 'sha256') -> str:
    """
    Calcule le hash d'un contenu en mémoire
    
    Args:
        content: Contenu binaire
        algorithm: Algorithme de hash
    
    Returns:
        Hash hexadécimal
    """
    hash_func = getattr(hashlib, algorithm)()
    hash_func.update(content)
    return hash_func.hexdigest()


# =================================================================
# NOMS DE FICHIERS SÉCURISÉS
# =================================================================

def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour le rendre sécurisé
    
    Supprime les caractères dangereux, les espaces, etc.
    
    Args:
        filename: Nom de fichier original
    
    Returns:
        Nom de fichier sécurisé
    """
    if not filename:
        return "unnamed_file"
    
    # Récupérer nom et extension
    path = Path(filename)
    name = path.stem
    ext = path.suffix
    
    # Remplacer caractères dangereux
    import re
    name = re.sub(r'[^\w\s\-.]', '', name)
    
    # Remplacer espaces par underscores
    name = name.replace(' ', '_')
    
    # Supprimer underscores multiples
    name = re.sub(r'_+', '_', name)
    
    # Limiter la longueur
    max_length = 200
    if len(name) > max_length:
        name = name[:max_length]
    
    # Reconstruire avec extension
    safe_filename = f"{name}{ext}".strip('_')
    
    return safe_filename or "unnamed_file"


def generate_unique_filename(
    filename: str,
    directory: Optional[Union[str, Path]] = None,
    timestamp: bool = True
) -> str:
    """
    Génère un nom de fichier unique
    
    Args:
        filename: Nom de fichier de base
        directory: Répertoire où vérifier l'unicité (optionnel)
        timestamp: Ajouter un timestamp
    
    Returns:
        Nom de fichier unique
    """
    # Nettoyer le nom
    safe_name = sanitize_filename(filename)
    path = Path(safe_name)
    name = path.stem
    ext = path.suffix
    
    # Ajouter timestamp si demandé
    if timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"{name}_{ts}"
    
    unique_name = f"{name}{ext}"
    
    # Si répertoire fourni, vérifier l'unicité
    if directory:
        directory = Path(directory)
        counter = 1
        
        while (directory / unique_name).exists():
            unique_name = f"{name}_{counter}{ext}"
            counter += 1
    
    return unique_name


# =================================================================
# GESTION DE RÉPERTOIRES
# =================================================================

def ensure_directory_exists(directory: Union[str, Path]) -> Path:
    """
    Crée un répertoire s'il n'existe pas
    
    Args:
        directory: Chemin du répertoire
    
    Returns:
        Path du répertoire
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def clean_directory(
    directory: Union[str, Path],
    older_than_days: Optional[int] = None,
    pattern: str = "*"
) -> int:
    """
    Nettoie un répertoire
    
    Args:
        directory: Répertoire à nettoyer
        older_than_days: Supprimer fichiers plus vieux que N jours (None = tous)
        pattern: Pattern de fichiers à supprimer (ex: '*.tmp')
    
    Returns:
        Nombre de fichiers supprimés
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        return 0
    
    deleted_count = 0
    cutoff_time = None
    
    if older_than_days is not None:
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(days=older_than_days)
    
    for file_path in dir_path.glob(pattern):
        if not file_path.is_file():
            continue
        
        # Vérifier l'âge si spécifié
        if cutoff_time:
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_mtime >= cutoff_time:
                continue
        
        try:
            file_path.unlink()
            deleted_count += 1
            logger.debug(f"Fichier supprimé: {file_path.name}")
        except Exception as e:
            logger.error(f"Erreur suppression {file_path}: {e}")
    
    return deleted_count


def get_directory_size(directory: Union[str, Path]) -> int:
    """
    Calcule la taille totale d'un répertoire
    
    Args:
        directory: Chemin du répertoire
    
    Returns:
        Taille en octets
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        return 0
    
    total_size = 0
    
    for file_path in dir_path.rglob('*'):
        if file_path.is_file():
            try:
                total_size += file_path.stat().st_size
            except:
                pass
    
    return total_size


# =================================================================
# FICHIERS TEMPORAIRES
# =================================================================

def create_temp_file(
    suffix: Optional[str] = None,
    prefix: Optional[str] = None,
    dir: Optional[Union[str, Path]] = None
) -> Path:
    """
    Crée un fichier temporaire
    
    Args:
        suffix: Suffixe du fichier (ex: '.pdf')
        prefix: Préfixe du fichier
        dir: Répertoire temporaire
    
    Returns:
        Path du fichier temporaire
    """
    fd, temp_path = tempfile.mkstemp(
        suffix=suffix,
        prefix=prefix,
        dir=str(dir) if dir else None
    )
    
    # Fermer le descripteur de fichier
    os.close(fd)
    
    return Path(temp_path)


def create_temp_directory(
    prefix: Optional[str] = None,
    dir: Optional[Union[str, Path]] = None
) -> Path:
    """
    Crée un répertoire temporaire
    
    Args:
        prefix: Préfixe du répertoire
        dir: Répertoire parent
    
    Returns:
        Path du répertoire temporaire
    """
    temp_dir = tempfile.mkdtemp(
        prefix=prefix,
        dir=str(dir) if dir else None
    )
    
    return Path(temp_dir)


# =================================================================
# COPIE ET DÉPLACEMENT
# =================================================================

def copy_file(
    source: Union[str, Path],
    destination: Union[str, Path],
    overwrite: bool = False
) -> bool:
    """
    Copie un fichier
    
    Args:
        source: Fichier source
        destination: Fichier destination
        overwrite: Écraser si existe déjà
    
    Returns:
        True si succès
    """
    source_path = Path(source)
    dest_path = Path(destination)
    
    if not source_path.exists():
        logger.error(f"Fichier source inexistant: {source_path}")
        return False
    
    if dest_path.exists() and not overwrite:
        logger.error(f"Destination existe déjà: {dest_path}")
        return False
    
    try:
        # Créer le répertoire parent si nécessaire
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copier
        shutil.copy2(source_path, dest_path)
        logger.debug(f"Fichier copié: {source_path.name} -> {dest_path}")
        return True
    
    except Exception as e:
        logger.error(f"Erreur copie {source_path} vers {dest_path}: {e}")
        return False


def move_file(
    source: Union[str, Path],
    destination: Union[str, Path],
    overwrite: bool = False
) -> bool:
    """
    Déplace un fichier
    
    Args:
        source: Fichier source
        destination: Fichier destination
        overwrite: Écraser si existe déjà
    
    Returns:
        True si succès
    """
    source_path = Path(source)
    dest_path = Path(destination)
    
    if not source_path.exists():
        logger.error(f"Fichier source inexistant: {source_path}")
        return False
    
    if dest_path.exists() and not overwrite:
        logger.error(f"Destination existe déjà: {dest_path}")
        return False
    
    try:
        # Créer le répertoire parent si nécessaire
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Déplacer
        shutil.move(str(source_path), str(dest_path))
        logger.debug(f"Fichier déplacé: {source_path.name} -> {dest_path}")
        return True
    
    except Exception as e:
        logger.error(f"Erreur déplacement {source_path} vers {dest_path}: {e}")
        return False


# =================================================================
# LECTURE/ÉCRITURE
# =================================================================

def read_file_content(file_path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
    """
    Lit le contenu textuel d'un fichier
    
    Args:
        file_path: Chemin du fichier
        encoding: Encodage (défaut: utf-8)
    
    Returns:
        Contenu du fichier ou None
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.error(f"Erreur lecture fichier {file_path}: {e}")
        return None


def read_file_bytes(file_path: Union[str, Path]) -> Optional[bytes]:
    """
    Lit le contenu binaire d'un fichier
    
    Args:
        file_path: Chemin du fichier
    
    Returns:
        Contenu binaire ou None
    """
    try:
        with open(file_path, 'rb') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Erreur lecture fichier {file_path}: {e}")
        return None


def write_file_content(
    file_path: Union[str, Path],
    content: str,
    encoding: str = 'utf-8',
    create_dirs: bool = True
) -> bool:
    """
    Écrit du contenu textuel dans un fichier
    
    Args:
        file_path: Chemin du fichier
        content: Contenu à écrire
        encoding: Encodage
        create_dirs: Créer les répertoires parents
    
    Returns:
        True si succès
    """
    file_path = Path(file_path)
    
    try:
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return True
    
    except Exception as e:
        logger.error(f"Erreur écriture fichier {file_path}: {e}")
        return False


def write_file_bytes(
    file_path: Union[str, Path],
    content: bytes,
    create_dirs: bool = True
) -> bool:
    """
    Écrit du contenu binaire dans un fichier
    
    Args:
        file_path: Chemin du fichier
        content: Contenu binaire
        create_dirs: Créer les répertoires parents
    
    Returns:
        True si succès
    """
    file_path = Path(file_path)
    
    try:
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return True
    
    except Exception as e:
        logger.error(f"Erreur écriture fichier {file_path}: {e}")
        return False


# =================================================================
# STATISTIQUES
# =================================================================

def get_file_stats(file_path: Union[str, Path]) -> Optional[Dict]:
    """
    Récupère les statistiques d'un fichier
    
    Returns:
        Dict avec size, created_at, modified_at, etc.
    """
    try:
        file_path = Path(file_path)
        stats = file_path.stat()
        
        return {
            'size': stats.st_size,
            'size_formatted': format_file_size(stats.st_size),
            'created_at': datetime.fromtimestamp(stats.st_ctime),
            'modified_at': datetime.fromtimestamp(stats.st_mtime),
            'accessed_at': datetime.fromtimestamp(stats.st_atime),
            'is_file': file_path.is_file(),
            'is_dir': file_path.is_dir(),
            'extension': get_file_extension(file_path.name),
            'mime_type': get_mime_type(file_path.name)
        }
    
    except Exception as e:
        logger.error(f"Erreur stats fichier {file_path}: {e}")
        return None