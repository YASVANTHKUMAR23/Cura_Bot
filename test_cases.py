import pytest
from datetime import datetime

from database.models import (
    Patient, DetectedDisease, Symptom, 
    IntensityLevel, RiskLevel, SeverityLevel
)
from utils.severity_calculator import calculate_severity
from utils.intensity_extractor import extract_intensity


class TestSeverityCalculator:
    """Test severity calculation matrix"""
    
    def test_critical_risk_severe(self):
        severity = calculate_severity(
            RiskLevel.CRITICAL_RISK,
            IntensityLevel.SEVERE
        )
        assert severity == SeverityLevel.CRITICAL
    
    def test_high_risk_mild(self):
        severity = calculate_severity(
            RiskLevel.HIGH_RISK,
            IntensityLevel.MILD
        )
        assert severity == SeverityLevel.MODERATE
    
    def test_low_risk_critical(self):
        severity = calculate_severity(
            RiskLevel.LOW_RISK,
            IntensityLevel.CRITICAL
        )
        assert severity == SeverityLevel.HIGH


class TestIntensityExtractor:
    """Test intensity extraction"""
    
    def test_severe_extraction(self):
        text = 'very severe crushing pain'
        intensity = extract_intensity(text)
        assert intensity in [IntensityLevel.SEVERE, IntensityLevel.CRITICAL]
    
    def test_mild_extraction(self):
        text = 'slight discomfort'
        intensity = extract_intensity(text)
        assert intensity == IntensityLevel.MILD


class TestDatabaseModels:
    """Test Pydantic models"""
    
    def test_patient_creation(self):
        patient = Patient(
            phone_number='+91-9876543210',
            name='Test Patient',
            age=35
        )
        assert patient.phone_number == '+91-9876543210'
        assert patient.name == 'Test Patient'
    
    def test_symptom_creation(self):
        symptom = Symptom(
            symptom='fever',
            intensity=IntensityLevel.SEVERE,
            description='High fever'
        )
        assert symptom.symptom == 'fever'
        assert symptom.intensity == IntensityLevel.SEVERE


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

