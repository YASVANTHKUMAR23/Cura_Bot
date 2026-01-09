from Cura_Bot.database.models import RiskLevel, IntensityLevel, SeverityLevel
from config import SEVERITY_MATRIX


def calculate_severity(risk_level: RiskLevel, 
                       intensity_level: IntensityLevel) -> SeverityLevel:
    """
    Calculate final severity using matrix lookup
    
    Args:
        risk_level: Disease risk level (CRITICAL_RISK, HIGH_RISK, etc.)
        intensity_level: Max symptom intensity (MILD, MODERATE, SEVERE, CRITICAL)
    
    Returns:
        Final severity level (MILD, MODERATE, HIGH, CRITICAL)
    """
    
    # Matrix lookup
    severity_value = SEVERITY_MATRIX[risk_level.value][intensity_level.value]
    
    return SeverityLevel[severity_value]


