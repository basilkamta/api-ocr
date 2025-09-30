"""
Utilitaires pour le traitement des dates
"""
import re
from datetime import datetime, date
from typing import Optional, List, Dict
from dateutil import parser as date_parser
import calendar

# =================================================================
# MOIS EN FRANÇAIS
# =================================================================

MOIS_FR = {
    'janvier': 1,
    'fevrier': 2,
    'février': 2,
    'mars': 3,
    'avril': 4,
    'mai': 5,
    'juin': 6,
    'juillet': 7,
    'aout': 8,
    'août': 8,
    'septembre': 9,
    'octobre': 10,
    'novembre': 11,
    'decembre': 12,
    'décembre': 12,
}

MOIS_FR_ABBR = {
    'janv': 1,
    'fev': 2,
    'févr': 2,
    'mars': 3,
    'avr': 4,
    'mai': 5,
    'juin': 6,
    'juil': 7,
    'juill': 7,
    'août': 8,
    'aout': 8,
    'sept': 9,
    'oct': 10,
    'nov': 11,
    'dec': 12,
    'déc': 12,
}

# =================================================================
# PARSING DE DATES
# =================================================================

def parse_french_date(date_str: str) -> Optional[datetime]:
    """
    Parse une date au format français
    
    Formats supportés:
    - JJ/MM/AAAA (15/12/2024)
    - JJ-MM-AAAA (15-12-2024)
    - JJ Mois AAAA (15 Décembre 2024)
    - JJ Mois. AAAA (15 Déc. 2024)
    """
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    # Format JJ/MM/AAAA ou JJ-MM-AAAA
    match = re.match(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', date_str)
    if match:
        try:
            day, month, year = map(int, match.groups())
            return datetime(year, month, day)
        except ValueError:
            pass
    
    # Format JJ Mois AAAA
    for mois, num in MOIS_FR.items():
        pattern = rf'(\d{{1,2}})\s+{mois}\s+(\d{{4}})'
        match = re.search(pattern, date_str, re.IGNORECASE)
        if match:
            try:
                day = int(match.group(1))
                year = int(match.group(2))
                return datetime(year, num, day)
            except ValueError:
                pass
    
    # Format JJ Mois. AAAA (abrégé)
    for mois, num in MOIS_FR_ABBR.items():
        pattern = rf'(\d{{1,2}})\s+{mois}\.?\s+(\d{{4}})'
        match = re.search(pattern, date_str, re.IGNORECASE)
        if match:
            try:
                day = int(match.group(1))
                year = int(match.group(2))
                return datetime(year, num, day)
            except ValueError:
                pass
    
    # Fallback: dateutil
    try:
        return date_parser.parse(date_str, dayfirst=True)
    except:
        return None


def parse_iso_date(date_str: str) -> Optional[datetime]:
    """
    Parse une date au format ISO (AAAA-MM-JJ)
    """
    if not date_str:
        return None
    
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None


def extract_dates_from_text(text: str) -> List[Dict]:
    """
    Extrait toutes les dates trouvées dans un texte
    
    Returns:
        Liste de dictionnaires {date: datetime, raw: str, format: str}
    """
    if not text:
        return []
    
    dates = []
    
    # Format JJ/MM/AAAA
    pattern_jj_mm_aaaa = r'\b(\d{2})[/\-](\d{2})[/\-](\d{4})\b'
    for match in re.finditer(pattern_jj_mm_aaaa, text):
        try:
            day, month, year = map(int, match.groups())
            dt = datetime(year, month, day)
            dates.append({
                'date': dt,
                'raw': match.group(0),
                'format': 'JJ/MM/AAAA',
                'position': match.start()
            })
        except ValueError:
            pass
    
    # Format AAAA-MM-JJ (ISO)
    pattern_iso = r'\b(\d{4})[/\-](\d{2})[/\-](\d{2})\b'
    for match in re.finditer(pattern_iso, text):
        try:
            year, month, day = map(int, match.groups())
            dt = datetime(year, month, day)
            dates.append({
                'date': dt,
                'raw': match.group(0),
                'format': 'AAAA-MM-JJ',
                'position': match.start()
            })
        except ValueError:
            pass
    
    # Format JJ Mois AAAA
    for mois, num in MOIS_FR.items():
        pattern = rf'\b(\d{{1,2}})\s+{mois}\s+(\d{{4}})\b'
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                day = int(match.group(1))
                year = int(match.group(2))
                dt = datetime(year, num, day)
                dates.append({
                    'date': dt,
                    'raw': match.group(0),
                    'format': 'JJ Mois AAAA',
                    'position': match.start()
                })
            except ValueError:
                pass
    
    # Trier par position dans le texte
    dates.sort(key=lambda x: x['position'])
    
    return dates


# =================================================================
# FORMATAGE DE DATES
# =================================================================

def format_date_french(dt: datetime) -> str:
    """
    Formate une date au format français (JJ/MM/AAAA)
    """
    if not dt:
        return ""
    
    return dt.strftime('%d/%m/%Y')


def format_date_iso(dt: datetime) -> str:
    """
    Formate une date au format ISO (AAAA-MM-JJ)
    """
    if not dt:
        return ""
    
    return dt.strftime('%Y-%m-%d')


def format_date_text(dt: datetime, with_day_name: bool = False) -> str:
    """
    Formate une date en texte français
    
    Ex: "15 décembre 2024" ou "Lundi 15 décembre 2024"
    """
    if not dt:
        return ""
    
    mois_names = [
        'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
        'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'
    ]
    
    mois = mois_names[dt.month - 1]
    result = f"{dt.day} {mois} {dt.year}"
    
    if with_day_name:
        jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        jour = jours[dt.weekday()]
        result = f"{jour} {result}"
    
    return result


# =================================================================
# VALIDATION DE DATES
# =================================================================

def is_valid_date(day: int, month: int, year: int) -> bool:
    """
    Vérifie si une date est valide
    """
    try:
        datetime(year, month, day)
        return True
    except ValueError:
        return False


def is_valid_date_range(start_date: datetime, end_date: datetime) -> bool:
    """
    Vérifie si un intervalle de dates est valide
    """
    if not start_date or not end_date:
        return False
    
    return start_date <= end_date


def is_fiscal_year_valid(year: int) -> bool:
    """
    Vérifie si une année fiscale est valide (entre 2015 et année actuelle + 2)
    """
    current_year = datetime.now().year
    return 2015 <= year <= current_year + 2


# =================================================================
# CALCULS SUR DATES
# =================================================================

def days_between(date1: datetime, date2: datetime) -> int:
    """
    Calcule le nombre de jours entre deux dates
    """
    if not date1 or not date2:
        return 0
    
    delta = date2 - date1
    return abs(delta.days)


def get_fiscal_year(dt: datetime) -> int:
    """
    Retourne l'année fiscale pour une date donnée
    
    Note: Au Cameroun, l'exercice fiscal = année civile
    """
    if not dt:
        return datetime.now().year
    
    return dt.year


def get_quarter(dt: datetime) -> int:
    """
    Retourne le trimestre (1-4) pour une date
    """
    if not dt:
        return 1
    
    return (dt.month - 1) // 3 + 1


def get_semester(dt: datetime) -> int:
    """
    Retourne le semestre (1-2) pour une date
    """
    if not dt:
        return 1
    
    return 1 if dt.month <= 6 else 2


# =================================================================
# UTILITAIRES SPÉCIFIQUES DOCUMENTS
# =================================================================

def extract_emission_date(text: str) -> Optional[datetime]:
    """
    Extrait la date d'émission d'un document
    
    Cherche des patterns comme:
    - Date d'émission: JJ/MM/AAAA
    - Émis le: JJ/MM/AAAA
    - Fait à ..., le JJ/MM/AAAA
    """
    if not text:
        return None
    
    patterns = [
        r"Date\s+d['\u2019]émission\s*[:]\s*(.+?)(?:\n|$)",
        r"Émis\s+le\s*[:]\s*(.+?)(?:\n|$)",
        r"Fait\s+à\s+.+?,?\s+le\s+(.+?)(?:\n|$)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            parsed = parse_french_date(date_str)
            if parsed:
                return parsed
    
    return None


def extract_payment_date(text: str) -> Optional[datetime]:
    """
    Extrait la date de paiement d'un document
    """
    if not text:
        return None
    
    patterns = [
        r"Date\s+de\s+paiement\s*[:]\s*(.+?)(?:\n|$)",
        r"Payé\s+le\s*[:]\s*(.+?)(?:\n|$)",
        r"Date\s+de\s+règlement\s*[:]\s*(.+?)(?:\n|$)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            parsed = parse_french_date(date_str)
            if parsed:
                return parsed
    
    return None


def extract_signature_date(text: str) -> Optional[datetime]:
    """
    Extrait la date de signature d'un document
    """
    if not text:
        return None
    
    patterns = [
        r"Signé\s+le\s*[:]\s*(.+?)(?:\n|$)",
        r"Date\s+de\s+signature\s*[:]\s*(.+?)(?:\n|$)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            parsed = parse_french_date(date_str)
            if parsed:
                return parsed
    
    return None


def categorize_date(dt: datetime) -> str:
    """
    Catégorise une date trouvée dans un document
    
    Returns: 'emission', 'paiement', 'signature', 'autre'
    """
    # Cette fonction nécessite du contexte
    # Pour l'instant, retourne 'autre'
    return 'autre'


# =================================================================
# NORMALISATION
# =================================================================

def normalize_date_format(date_str: str) -> Optional[str]:
    """
    Normalise une date en format ISO (AAAA-MM-JJ)
    
    Accepte différents formats en entrée
    """
    if not date_str:
        return None
    
    parsed = parse_french_date(date_str)
    if parsed:
        return format_date_iso(parsed)
    
    return None


def dates_are_equal(date1: datetime, date2: datetime, ignore_time: bool = True) -> bool:
    """
    Compare deux dates
    
    Args:
        date1: Première date
        date2: Deuxième date
        ignore_time: Si True, compare seulement année/mois/jour
    """
    if not date1 or not date2:
        return False
    
    if ignore_time:
        return date1.date() == date2.date()
    else:
        return date1 == date2