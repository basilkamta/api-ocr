"""
Utilitaires pour les patterns regex et extraction de données
"""
import re
from typing import List, Dict, Optional, Pattern
from dataclasses import dataclass

@dataclass
class RegexPattern:
    """Pattern regex avec métadonnées"""
    pattern: Pattern
    name: str
    priority: int = 0
    description: str = ""

class PatternMatcher:
    """Gestionnaire de patterns regex avec priorités"""
    
    # =================================================================
    # PATTERNS POUR DOCUMENTS ADMINISTRATIFS CAMEROUNAIS
    # =================================================================
    
    # Patterns Mandat (MD/XXXXXXX)
    MANDAT_PATTERNS = [
        # Format standard: MD/2412034
        RegexPattern(
            pattern=re.compile(r'MD[/\\-](\d{7})', re.IGNORECASE),
            name="mandat_standard",
            priority=10,
            description="Format MD/XXXXXXX"
        ),
        # Avec N° ou Numéro
        RegexPattern(
            pattern=re.compile(r'N[°o]?\s*(?:Mandat|MANDAT)[:\s]*MD[/\\-](\d{7})', re.IGNORECASE),
            name="mandat_with_label",
            priority=9,
            description="N° Mandat: MD/XXXXXXX"
        ),
        # Variations avec espaces
        RegexPattern(
            pattern=re.compile(r'MD\s+(\d{7})', re.IGNORECASE),
            name="mandat_with_space",
            priority=5,
            description="MD XXXXXXX"
        ),
        # OCR peut confondre M et N, D et O
        RegexPattern(
            pattern=re.compile(r'[MN][DO][/\\-](\d{7})', re.IGNORECASE),
            name="mandat_ocr_variant",
            priority=3,
            description="Variantes OCR (MD/ND/MO/NO)"
        ),
    ]
    
    # Patterns Bordereau (BOR/XXXXXXX)
    BORDEREAU_PATTERNS = [
        # Format standard: BOR/2402756
        RegexPattern(
            pattern=re.compile(r'BOR[/\\-](\d{7})', re.IGNORECASE),
            name="bordereau_standard",
            priority=10,
            description="Format BOR/XXXXXXX"
        ),
        # Avec N° ou Numéro
        RegexPattern(
            pattern=re.compile(r'N[°o]?\s*(?:Bordereau|BORDEREAU)[:\s]*BOR[/\\-](\d{7})', re.IGNORECASE),
            name="bordereau_with_label",
            priority=9,
            description="N° Bordereau: BOR/XXXXXXX"
        ),
        # Variations
        RegexPattern(
            pattern=re.compile(r'BOR\s+(\d{7})', re.IGNORECASE),
            name="bordereau_with_space",
            priority=5,
            description="BOR XXXXXXX"
        ),
        # OCR peut confondre B et 8
        RegexPattern(
            pattern=re.compile(r'[B8]OR[/\\-](\d{7})', re.IGNORECASE),
            name="bordereau_ocr_variant",
            priority=3,
            description="Variantes OCR (BOR/8OR)"
        ),
    ]
    
    # Patterns Exercice Fiscal
    EXERCICE_PATTERNS = [
        # Avec label: Exercice: 2024
        RegexPattern(
            pattern=re.compile(r'(?:Exercice|EXERCICE)[:\s]+(\d{4})', re.IGNORECASE),
            name="exercice_with_label",
            priority=10,
            description="Exercice: YYYY"
        ),
        # Année seule (contexte document)
        RegexPattern(
            pattern=re.compile(r'\b(20[1-3][0-9])\b'),
            name="exercice_year_only",
            priority=5,
            description="Année YYYY"
        ),
        # Gestion budgétaire: GB/2024
        RegexPattern(
            pattern=re.compile(r'GB[/\\-](\d{4})', re.IGNORECASE),
            name="exercice_gb",
            priority=8,
            description="GB/YYYY"
        ),
    ]
    
    # Patterns Dates (format français)
    DATE_PATTERNS = [
        # JJ/MM/AAAA
        RegexPattern(
            pattern=re.compile(r'\b(\d{2})[/\\-](\d{2})[/\\-](\d{4})\b'),
            name="date_jj_mm_aaaa",
            priority=10,
            description="JJ/MM/AAAA"
        ),
        # JJ Mois AAAA (ex: 15 Décembre 2024)
        RegexPattern(
            pattern=re.compile(
                r'\b(\d{1,2})\s+(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s+(\d{4})\b',
                re.IGNORECASE
            ),
            name="date_texte",
            priority=9,
            description="JJ Mois AAAA"
        ),
        # AAAA-MM-JJ (ISO)
        RegexPattern(
            pattern=re.compile(r'\b(\d{4})[/\\-](\d{2})[/\\-](\d{2})\b'),
            name="date_iso",
            priority=8,
            description="AAAA-MM-JJ"
        ),
    ]
    
    # Patterns Montants (FCFA)
    AMOUNT_PATTERNS = [
        # Format avec espaces: 5 672 860
        RegexPattern(
            pattern=re.compile(r'\b([\d\s]+)\s*(?:FCFA|F\s*CFA|francs?\s*CFA)\b', re.IGNORECASE),
            name="amount_with_spaces",
            priority=10,
            description="X XXX XXX FCFA"
        ),
        # Format avec virgules ou points: 5,672,860 ou 5.672.860
        RegexPattern(
            pattern=re.compile(r'\b([\d,\.]+)\s*(?:FCFA|F\s*CFA)\b', re.IGNORECASE),
            name="amount_with_separators",
            priority=9,
            description="X,XXX,XXX FCFA"
        ),
        # Montant: ou Total:
        RegexPattern(
            pattern=re.compile(r'(?:Montant|Total|Somme)[:\s]+([\d\s,\.]+)\s*(?:FCFA)?', re.IGNORECASE),
            name="amount_with_label",
            priority=8,
            description="Montant: X XXX XXX"
        ),
    ]
    
    # Patterns Bénéficiaire
    BENEFICIAIRE_PATTERNS = [
        RegexPattern(
            pattern=re.compile(r'(?:Bénéficiaire|Beneficiaire|BENEFICIAIRE)[:\s]+([A-ZÀ-Ÿ\s]+(?:\n[A-ZÀ-Ÿ\s]+)*)', re.IGNORECASE),
            name="beneficiaire_with_label",
            priority=10,
            description="Bénéficiaire: NOM"
        ),
    ]
    
    @classmethod
    def find_all_matches(cls, text: str, patterns: List[RegexPattern]) -> List[Dict]:
        """
        Trouve toutes les correspondances pour une liste de patterns
        
        Returns:
            Liste de {match, pattern_name, priority, start, end, groups}
        """
        matches = []
        
        for pattern_obj in patterns:
            for match in pattern_obj.pattern.finditer(text):
                matches.append({
                    'match': match.group(0),
                    'groups': match.groups(),
                    'pattern_name': pattern_obj.name,
                    'priority': pattern_obj.priority,
                    'start': match.start(),
                    'end': match.end(),
                    'description': pattern_obj.description
                })
        
        # Trier par priorité décroissante
        matches.sort(key=lambda x: x['priority'], reverse=True)
        
        return matches
    
    @classmethod
    def find_best_match(cls, text: str, patterns: List[RegexPattern]) -> Optional[Dict]:
        """Trouve la meilleure correspondance (plus haute priorité)"""
        matches = cls.find_all_matches(text, patterns)
        return matches[0] if matches else None
    
    @classmethod
    def extract_mandat(cls, text: str) -> Optional[str]:
        """Extrait le numéro de mandat"""
        match = cls.find_best_match(text, cls.MANDAT_PATTERNS)
        if match and match['groups']:
            return match['groups'][0]
        return None
    
    @classmethod
    def extract_bordereau(cls, text: str) -> Optional[str]:
        """Extrait le numéro de bordereau"""
        match = cls.find_best_match(text, cls.BORDEREAU_PATTERNS)
        if match and match['groups']:
            return match['groups'][0]
        return None
    
    @classmethod
    def extract_exercice(cls, text: str) -> Optional[str]:
        """Extrait l'exercice fiscal"""
        match = cls.find_best_match(text, cls.EXERCICE_PATTERNS)
        if match and match['groups']:
            year = match['groups'][0]
            # Validation: année entre 2015 et 2030
            if year.isdigit() and 2015 <= int(year) <= 2030:
                return year
        return None
    
    @classmethod
    def extract_all_dates(cls, text: str) -> List[str]:
        """Extrait toutes les dates trouvées"""
        dates = []
        matches = cls.find_all_matches(text, cls.DATE_PATTERNS)
        
        for match in matches:
            date_str = match['match']
            dates.append(date_str)
        
        return dates
    
    @classmethod
    def extract_all_amounts(cls, text: str) -> List[str]:
        """Extrait tous les montants trouvés"""
        amounts = []
        matches = cls.find_all_matches(text, cls.AMOUNT_PATTERNS)
        
        for match in matches:
            amount_str = match['groups'][0] if match['groups'] else match['match']
            amounts.append(amount_str)
        
        return amounts
    
    @classmethod
    def validate_mandat_format(cls, number: str) -> bool:
        """Valide le format d'un numéro de mandat"""
        if not number or not number.isdigit():
            return False
        
        if len(number) != 7:
            return False
        
        # Vérifier le préfixe année (24, 23, 22, etc.)
        year_prefix = number[:2]
        return year_prefix in ['24', '23', '22', '21', '20', '19', '25', '26']
    
    @classmethod
    def validate_bordereau_format(cls, number: str) -> bool:
        """Valide le format d'un numéro de bordereau"""
        return cls.validate_mandat_format(number)  # Même format


# =================================================================
# FONCTIONS UTILITAIRES
# =================================================================

def clean_ocr_text(text: str) -> str:
    """
    Nettoie le texte OCR des erreurs communes
    
    - Supprime caractères parasites
    - Normalise espaces
    - Corrige erreurs OCR courantes
    """
    if not text:
        return ""
    
    # Normaliser espaces
    text = re.sub(r'\s+', ' ', text)
    
    # Corrections OCR courantes
    corrections = {
        'l\/': '/',
        '\\/': '/',
        '|': 'I',
        '0O': '00',
        'O0': '00',
    }
    
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)
    
    return text.strip()


def normalize_amount(amount_str: str) -> Optional[float]:
    """
    Normalise un montant extrait en float
    
    Ex: "5 672 860" -> 5672860.0
        "5,672,860" -> 5672860.0
    """
    if not amount_str:
        return None
    
    # Supprimer FCFA et autres suffixes
    amount_str = re.sub(r'(?:FCFA|F\s*CFA|francs?\s*CFA)', '', amount_str, flags=re.IGNORECASE)
    
    # Supprimer espaces, virgules, points (sauf dernier point pour décimales)
    amount_str = amount_str.strip()
    amount_str = amount_str.replace(' ', '')
    amount_str = amount_str.replace(',', '')
    
    # Gérer le cas des décimales avec point
    parts = amount_str.split('.')
    if len(parts) > 2:
        # Plusieurs points: supprimer tous sauf le dernier
        amount_str = ''.join(parts[:-1]) + '.' + parts[-1]
    
    try:
        return float(amount_str)
    except ValueError:
        return None


def format_mandat_reference(number: str) -> str:
    """Formate un numéro de mandat en référence complète"""
    return f"MD/{number}"


def format_bordereau_reference(number: str) -> str:
    """Formate un numéro de bordereau en référence complète"""
    return f"BOR/{number}"