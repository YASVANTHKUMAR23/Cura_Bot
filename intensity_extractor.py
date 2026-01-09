import re
from typing import List, Dict
from Cura_Bot.database.models import IntensityLevel


# Intensity keywords mapping
INTENSITY_KEYWORDS = {
    'CRITICAL': ['unbearable', 'worst ever', 'extreme', "can't breathe", 'can\'t move', 'collapsing'],
    'SEVERE': ['severe', 'very bad', 'terrible', 'intense', 'excruciating', 'overwhelming'],
    'MODERATE': ['moderate', 'bad', 'significant', 'noticeable', 'uncomfortable'],
    'MILD': ['mild', 'slight', 'little', 'minor', 'tolerable']
}


def extract_symptoms_with_intensity(text: str) -> List[Dict]:
    """
    Extract symptoms with intensity from text
    
    Args:
        text: User message
    
    Returns:
        List of dicts with 'symptom', 'intensity', 'description'
    """
    
    text_lower = text.lower()
    symptoms = []
    
    # Common symptoms
    symptom_patterns = {
        'fever': r'fever|temperature|hot',
        'cough': r'cough|coughing',
        'headache': r'headache|head pain|head hurts',
        'chest pain': r'chest pain|chest hurt',
        'breathing difficulty': r'breath|breathing|shortness of breath|can\'t breathe',
        'nausea': r'nausea|sick|vomit',
        'fatigue': r'tired|fatigue|weak|exhausted',
        'body pain': r'body pain|body ache|muscle pain',
        'sore throat': r'sore throat|throat pain',
        'dizziness': r'dizzy|lightheaded',
        'abdominal pain': r'stomach pain|abdominal pain|belly hurt'
    }
    
    for symptom, pattern in symptom_patterns.items():
        if re.search(pattern, text_lower):
            intensity = extract_intensity(text)
            symptoms.append({
                'symptom': symptom,
                'intensity': intensity.value,
                'description': text[:100]
            })
    
    return symptoms


def extract_intensity(text: str) -> IntensityLevel:
    """
    Extract intensity level from text
    
    Args:
        text: User message
    
    Returns:
        IntensityLevel enum
    """
    
    text_lower = text.lower()
    
    # Check in order of severity (highest first)
    for level in ['CRITICAL', 'SEVERE', 'MODERATE', 'MILD']:
        keywords = INTENSITY_KEYWORDS[level]
        if any(keyword in text_lower for keyword in keywords):
            return IntensityLevel[level]
    
    # Default to MODERATE
    return IntensityLevel.MODERATE


