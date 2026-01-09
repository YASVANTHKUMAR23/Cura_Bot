"""
Pydantic models for CuraBot system
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

#  PATIENT MODELS 

class PatientCreate(BaseModel):
    phone: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None

class PatientResponse(BaseModel):
    patient_id: UUID
    phone: str
    name: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    location: Optional[str]
    created_at: datetime

#  SESSION MODELS 

class SessionCreate(BaseModel):
    patient_id: UUID
    status: str = "active"
    symptoms_collected: Dict[str, Any] = {}

class SessionResponse(BaseModel):
    session_id: UUID
    patient_id: UUID
    status: str
    symptoms_collected: Dict[str, Any]
    disease_identified: Optional[str]
    confidence_score: Optional[float]
    severity_level: Optional[str]
    severity_score: Optional[int]
    emergency_call_requested: bool
    created_at: datetime
    completed_at: Optional[datetime]

class SessionUpdate(BaseModel):
    status: Optional[str] = None
    symptoms_collected: Optional[Dict[str, Any]] = None
    disease_identified: Optional[str] = None
    confidence_score: Optional[float] = None
    severity_level: Optional[str] = None
    severity_score: Optional[int] = None
    emergency_call_requested: Optional[bool] = None
    completed_at: Optional[datetime] = None

#  SYMPTOM MODELS 

class SymptomLog(BaseModel):
    session_id: UUID
    symptom_name: str
    severity: Optional[str] = None
    duration: Optional[str] = None
    additional_details: Optional[Dict[str, Any]] = None

class SymptomResponse(BaseModel):
    symptom_id: UUID
    session_id: UUID
    symptom_name: str
    severity: Optional[str]
    duration: Optional[str]
    additional_details: Optional[Dict[str, Any]]
    detected_at: datetime

#  DISEASE MODELS 

class DiseaseMatch(BaseModel):
    disease_id: UUID
    disease_name: str
    confidence: float
    matched_symptoms: List[str]
    total_symptoms: int

class DiseaseSymptom(BaseModel):
    symptom_name: str
    importance: str
    clarifying_question: str

class SeverityRule(BaseModel):
    symptom_name: str
    severity_level: str
    weight_points: int
    emergency_criteria: Optional[str]

#  DOCTOR MODELS 

class DoctorResponse(BaseModel):
    doctor_id: UUID
    name: str
    specialty: str
    location: str
    available: bool
    phone: str
    rating: float
    next_available_slot: Optional[datetime]

#  APPOINTMENT MODELS 

class AppointmentCreate(BaseModel):
    patient_id: UUID
    doctor_id: UUID
    session_id: UUID
    appointment_date: datetime
    severity_level: str
    summary: str
    emergency_booking: bool = False

class AppointmentResponse(BaseModel):
    appointment_id: UUID
    patient_id: UUID
    doctor_id: UUID
    session_id: UUID
    appointment_date: datetime
    severity_level: str
    status: str
    summary: str
    emergency_booking: bool
    created_at: datetime

#  CHAT MODELS 

class ChatMessage(BaseModel):
    appointment_id: UUID
    sender: str  # 'doctor', 'patient', 'ai_agent'
    message: str

class ChatResponse(BaseModel):
    chat_id: UUID
    appointment_id: UUID
    sender: str
    message: str
    sent_at: datetime

#  API REQUEST/RESPONSE MODELS 

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    phone: str
    user_name: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    severity_level: Optional[str] = None
    disease_suggested: Optional[str] = None
    confidence: Optional[float] = None
    requires_action: bool = False
    action_type: Optional[str] = None  # 'emergency_call', 'book_appointment', 'self_care'
    
class AgentState(BaseModel):
    """State passed between agents"""
    query: str
    session_id: str
    patient_id: UUID
    phone: str
    chat_history: List[Dict[str, str]] = []
    
    # Symptom tracking
    symptoms_collected: Dict[str, Any] = {}
    symptom_count: int = 0
    needs_more_symptoms: bool = True
    
    # Disease matching
    possible_diseases: List[DiseaseMatch] = []
    disease_identified: Optional[str] = None
    confidence_score: Optional[float] = None
    
    # Questions
    clarifying_questions: List[str] = []
    current_question_index: int = 0
    
    # Severity
    severity_level: Optional[str] = None
    severity_score: Optional[int] = None
    
    # Safety
    safety_status: str = "SAFE"  # SAFE, UNSAFE, EMERGENCY
    emergency_call_requested: bool = False
    
    # Response
    response: str = ""
    requires_action: bool = False
    action_type: Optional[str] = None
