"""
Utilitaires pour le traitement et nettoyage de texte
"""
import re
import unicodedata
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher

# =================================================================
# NETTOYAGE DE TEXTE
# =================================================================

def normalize_text(text: str) -> str:
    """
    Normalise le texte (minuscules, accents, espaces)
    """
    if not text:
        return ""
    
    # Supprimer les accents
    text = remove_accents(text)
    
    # Minuscules
    text = text.lower()
    
    # Normaliser espaces
    text = normalize_whitespace(text)
    
    return text


def remove_accents(text: str) -> str:
    """
    Supprime les accents des caractères
    
    Ex: "Bénéficiaire" -> "Beneficiaire"
    """
    if not text:
        return ""
    
    # Décomposition unicode (NFD = Normalization Form Decomposed)
    nfkd = unicodedata.normalize('NFD', text)
    
    # Supprimer les marques de combinaison (accents)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)])


def normalize_whitespace(text: str) -> str:
    """
    Normalise les espaces (multiples, tabulations, retours ligne)
    """
    if not text:
        return ""
    
    # Remplacer tabulations et retours ligne par espaces
    text = re.sub(r'[\t\n\r]+', ' ', text)
    
    # Remplacer espaces multiples par un seul
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def clean_ocr_artifacts(text: str) -> str:
    """
    Supprime les artéfacts OCR courants
    
    - Caractères parasites
    - Mauvaises reconnaissances
    - Caractères spéciaux inutiles
    """
    if not text:
        return ""
    
    # Supprimer caractères de contrôle
    text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\n\t ')
    
    # Corrections OCR courantes
    corrections = {
        '|': 'I',
        '¡': 'i',
        '§': 'S',
        '©': 'O',
        '®': 'R',
        '°': 'o',
        'º': 'o',
        '¹': '1',
        '²': '2',
        '³': '3',
        '×': 'x',
    }
    
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)
    
    return text


# =================================================================
# EXTRACTION DE ZONES
# =================================================================

def extract_lines(text: str) -> List[str]:
    """Divise le texte en lignes (sans lignes vides)"""
    if not text:
        return []
    
    lines = text.split('\n')
    return [line.strip() for line in lines if line.strip()]


def extract_words(text: str) -> List[str]:
    """Divise le texte en mots"""
    if not text:
        return []
    
    # Séparateurs: espaces et ponctuation
    words = re.findall(r'\b\w+\b', text)
    return words


def extract_sentences(text: str) -> List[str]:
    """Divise le texte en phrases"""
    if not text:
        return []
    
    # Séparateurs de phrases
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]


def extract_section(text: str, start_pattern: str, end_pattern: Optional[str] = None) -> Optional[str]:
    """
    Extrait une section du texte entre deux patterns
    
    Args:
        text: Texte source
        start_pattern: Pattern de début (regex)
        end_pattern: Pattern de fin (regex), si None prend jusqu'à la fin
    
    Returns:
        Section extraite ou None
    """
    if not text:
        return None
    
    start_match = re.search(start_pattern, text, re.IGNORECASE)
    if not start_match:
        return None
    
    start_pos = start_match.end()
    
    if end_pattern:
        end_match = re.search(end_pattern, text[start_pos:], re.IGNORECASE)
        if end_match:
            end_pos = start_pos + end_match.start()
            return text[start_pos:end_pos].strip()
    
    return text[start_pos:].strip()


# =================================================================
# COMPARAISON ET SIMILARITÉ
# =================================================================

def similarity_ratio(text1: str, text2: str) -> float:
    """
    Calcule la similarité entre deux textes (0.0 à 1.0)
    
    Utilise l'algorithme de Ratcliff/Obershelp
    """
    if not text1 or not text2:
        return 0.0
    
    # Normaliser avant comparaison
    text1 = normalize_text(text1)
    text2 = normalize_text(text2)
    
    return SequenceMatcher(None, text1, text2).ratio()


def fuzzy_match(text: str, pattern: str, threshold: float = 0.8) -> bool:
    """
    Vérifie si un pattern correspond approximativement à un texte
    
    Args:
        text: Texte à vérifier
        pattern: Pattern à chercher
        threshold: Seuil de similarité (0.0 à 1.0)
    
    Returns:
        True si similarité >= threshold
    """
    if not text or not pattern:
        return False
    
    return similarity_ratio(text, pattern) >= threshold


def find_similar_words(word: str, word_list: List[str], threshold: float = 0.8) -> List[Tuple[str, float]]:
    """
    Trouve les mots similaires dans une liste
    
    Returns:
        Liste de (mot, score_similarité) triée par similarité décroissante
    """
    if not word or not word_list:
        return []
    
    similarities = []
    for candidate in word_list:
        score = similarity_ratio(word, candidate)
        if score >= threshold:
            similarities.append((candidate, score))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities


# =================================================================
# FORMATAGE
# =================================================================

def capitalize_words(text: str) -> str:
    """
    Capitalise la première lettre de chaque mot
    
    Ex: "jean dupont" -> "Jean Dupont"
    """
    if not text:
        return ""
    
    return ' '.join(word.capitalize() for word in text.split())


def format_reference(prefix: str, number: str, separator: str = '/') -> str:
    """
    Formate une référence document
    
    Ex: format_reference("MD", "2412034") -> "MD/2412034"
    """
    return f"{prefix}{separator}{number}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Tronque un texte à une longueur maximale
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


# =================================================================
# VALIDATION
# =================================================================

def contains_digits(text: str) -> bool:
    """Vérifie si le texte contient des chiffres"""
    return bool(re.search(r'\d', text))


def contains_letters(text: str) -> bool:
    """Vérifie si le texte contient des lettres"""
    return bool(re.search(r'[a-zA-ZÀ-ÿ]', text))


def is_numeric(text: str) -> bool:
    """Vérifie si le texte est entièrement numérique"""
    if not text:
        return False
    
    # Supprimer espaces et séparateurs
    clean = text.replace(' ', '').replace(',', '').replace('.', '')
    return clean.isdigit()


def is_alphanumeric(text: str) -> bool:
    """Vérifie si le texte est alphanumérique"""
    if not text:
        return False
    
    return bool(re.match(r'^[a-zA-Z0-9]+$', text))


# =================================================================
# EXTRACTION DE MÉTADONNÉES
# =================================================================

def extract_uppercase_words(text: str, min_length: int = 3) -> List[str]:
    """
    Extrait les mots en majuscules (noms propres potentiels)
    """
    if not text:
        return []
    
    # Trouver mots de min_length lettres ou plus en majuscules
    pattern = rf'\b[A-ZÀ-Ÿ]{{{min_length},}}\b'
    return re.findall(pattern, text)


def extract_capitalized_sequences(text: str) -> List[str]:
    """
    Extrait les séquences de mots capitalisés (noms complets potentiels)
    
    Ex: "Jean Dupont" dans "Le bénéficiaire Jean Dupont habite..."
    """
    if not text:
        return []
    
    # Séquence de 2+ mots capitalisés
    pattern = r'\b(?:[A-ZÀ-Ÿ][a-zà-ÿ]+\s+){1,}[A-ZÀ-Ÿ][a-zà-ÿ]+\b'
    return re.findall(pattern, text)


def count_words(text: str) -> int:
    """Compte le nombre de mots"""
    if not text:
        return 0
    
    return len(extract_words(text))


def count_characters(text: str, include_spaces: bool = False) -> int:
    """Compte le nombre de caractères"""
    if not text:
        return 0
    
    if include_spaces:
        return len(text)
    else:
        return len(text.replace(' ', ''))


# =================================================================
# UTILITAIRES SPÉCIFIQUES DOCUMENTS ADMINISTRATIFS
# =================================================================

def extract_reference_numbers(text: str) -> List[str]:
    """
    Extrait tous les numéros de référence potentiels
    
    Format: LETTRES/CHIFFRES ou LETTRES-CHIFFRES
    """
    if not text:
        return []
    
    pattern = r'\b[A-Z]{2,4}[/\\-]\d{4,10}\b'
    return re.findall(pattern, text)


def standardize_reference_format(reference: str) -> str:
    """
    Standardise le format d'une référence
    
    Ex: "MD-2412034" -> "MD/2412034"
        "md/2412034" -> "MD/2412034"
    """
    if not reference:
        return ""
    
    # Remplacer \ et - par /
    reference = reference.replace('\\', '/').replace('-', '/')
    
    # Majuscules
    reference = reference.upper()
    
    return reference