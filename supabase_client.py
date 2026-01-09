"""
Supabase Client for CuraBot
Handles all database operations for Agent 2, 3, 4
"""
import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from supabase import create_client, Client
from dotenv import load_dotenv, find_dotenv

def load_environment():
    """Load .env from multiple possible locations"""
    logger = logging.getLogger(__name__)
    
    # Try find_dotenv first (searches upwards automatically)
    env_file = find_dotenv()
    if env_file:
        load_dotenv(env_file)
        logger.info(f"✅ Loaded .env from {env_file}")
        return True
    
    # Try multiple possible paths
    possible_paths = [
        ".env",  # Current directory
        os.path.join(os.path.dirname(__file__), ".env"),  # Same as this file
        os.path.join(os.path.dirname(__file__), "..", ".env"),  # Parent (Cura_Bot)
        os.path.join(os.path.dirname(__file__), "..", "..", ".env"),  # Grandparent (CuraBot root)
    ]
    
    for path in possible_paths:
        full_path = os.path.abspath(path)
        if os.path.exists(full_path):
            load_dotenv(full_path)
            logger.info(f"✅ Loaded .env from {full_path}")
            return True
    
    logger.warning("⚠️ No .env file found in any location")
    logger.warning("Searched paths:")
    for path in possible_paths:
        logger.warning(f"  - {os.path.abspath(path)}")
    return False

# Load environment variables
load_environment()

from database.models import (
    PatientCreate, PatientResponse,
    SessionCreate, SessionResponse, SessionUpdate,
    SymptomLog, SymptomResponse,
    DiseaseMatch, DiseaseSymptom, SeverityRule,
    DoctorResponse, AppointmentCreate, AppointmentResponse
)

logger = logging.getLogger(__name__)


class SupabaseClient:
    def __init__(self):
        """Initialize Supabase client"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("❌ SUPABASE_URL and SUPABASE_KEY must be set in .env")
            logger.error(f"SUPABASE_URL exists: {bool(supabase_url)}")
            logger.error(f"SUPABASE_KEY exists: {bool(supabase_key)}")
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        
        self.client: Client = create_client(supabase_url, supabase_key)
        logger.info("✅ Supabase client initialized")

    #  PATIENT OPERATIONS 
    
    def get_or_create_patient(self, phone: str, name: Optional[str] = None) -> PatientResponse:
        """Get existing patient or create new one"""
        try:
            # Check if patient exists
            response = self.client.table("patients").select("*").eq("phone", phone).execute()
            
            if response.data:
                logger.info(f"👤 Existing patient found: {phone}")
                return PatientResponse(**response.data[0])
            
            # Create new patient
            patient_data = {
                "phone": phone,
                "name": name
            }
            response = self.client.table("patients").insert(patient_data).execute()
            logger.info(f"✨ New patient created: {phone}")
            return PatientResponse(**response.data[0])
            
        except Exception as e:
            logger.error(f"❌ Error in get_or_create_patient: {e}")
            raise

    #  SESSION OPERATIONS 
    
    def get_active_session(self, patient_id: UUID) -> Optional[SessionResponse]:
        """Get active session for patient"""
        try:
            response = self.client.table("conversation_sessions") \
                .select("*") \
                .eq("patient_id", str(patient_id)) \
                .eq("status", "active") \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            
            if response.data:
                logger.info(f"📝 Active session found for patient {patient_id}")
                return SessionResponse(**response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting active session: {e}")
            return None

    def create_session(self, patient_id: UUID) -> SessionResponse:
        """Create new conversation session"""
        try:
            session_data = {
                "patient_id": str(patient_id),
                "status": "active",
                "symptoms_collected": {},
                "emergency_call_requested": False
            }
            response = self.client.table("conversation_sessions") \
                .insert(session_data) \
                .execute()
            logger.info(f"✨ New session created for patient {patient_id}")
            return SessionResponse(**response.data[0])
            
        except Exception as e:
            logger.error(f"❌ Error creating session: {e}")
            raise

    def update_session(self, session_id: UUID, updates: SessionUpdate) -> SessionResponse:
        """Update conversation session"""
        try:
            update_data = updates.dict(exclude_none=True)
            
            # Convert UUID to string if present
            if "session_id" in update_data:
                update_data["session_id"] = str(update_data["session_id"])
            
            response = self.client.table("conversation_sessions") \
                .update(update_data) \
                .eq("session_id", str(session_id)) \
                .execute()
            logger.info(f"✅ Session updated: {session_id}")
            return SessionResponse(**response.data[0])
            
        except Exception as e:
            logger.error(f"❌ Error updating session: {e}")
            raise

    def get_recent_sessions(self, patient_id: UUID, days: int = 7) -> List[SessionResponse]:
        """Get recent completed sessions for follow-ups"""
        try:
            response = self.client.table("conversation_sessions") \
                .select("*") \
                .eq("patient_id", str(patient_id)) \
                .in_("status", ["completed", "appointment_booked"]) \
                .gte("created_at", f"now() - interval '{days} days'") \
                .order("created_at", desc=True) \
                .execute()
            return [SessionResponse(**session) for session in response.data]
            
        except Exception as e:
            logger.error(f"❌ Error getting recent sessions: {e}")
            return []

    #  SYMPTOM OPERATIONS 
    
    def log_symptom(self, symptom: SymptomLog) -> SymptomResponse:
        """Log a symptom to database"""
        try:
            symptom_data = {
                "session_id": str(symptom.session_id),
                "symptom_name": symptom.symptom_name,
                "severity": symptom.severity,
                "duration": symptom.duration,
                "additional_details": symptom.additional_details or {}
            }
            response = self.client.table("symptoms_log") \
                .insert(symptom_data) \
                .execute()
            logger.info(f"📋 Symptom logged: {symptom.symptom_name}")
            return SymptomResponse(**response.data[0])
            
        except Exception as e:
            logger.error(f"❌ Error logging symptom: {e}")
            raise

    def get_session_symptoms(self, session_id: UUID) -> List[SymptomResponse]:
        """Get all symptoms for a session"""
        try:
            response = self.client.table("symptoms_log") \
                .select("*") \
                .eq("session_id", str(session_id)) \
                .order("detected_at", desc=False) \
                .execute()
            return [SymptomResponse(**symptom) for symptom in response.data]
            
        except Exception as e:
            logger.error(f"❌ Error getting symptoms: {e}")
            return []

    #  DISEASE MATCHING OPERATIONS 
    
    def match_diseases(self, symptoms: List[str], min_confidence: float = 0.3) -> List[DiseaseMatch]:
        """Match symptoms to diseases from database"""
        try:
            # Normalize symptoms to lower-case for matching
            symptoms = [s.lower().strip() for s in symptoms]
            logger.info(f"🔍 Matching diseases for symptoms: {symptoms} (min_conf={min_confidence})")
            
            # Try RPC first (if defined in Supabase)
            try:
                response = self.client.rpc("match_diseases_function", {
                    "symptom_list": symptoms,
                    "min_conf": min_confidence
                }).execute()
            except Exception as rpc_err:
                logger.warning(f"⚠️ RPC match_diseases_function not available or failed: {rpc_err}")
                response = type('Obj', (), {'data': None})  # Dummy object
            
            # If RPC doesn't exist or returns nothing, use fallback
            if not getattr(response, 'data', None):
                logger.info("ℹ️ RPC returned no data, using manual disease match")
                return self.manual_disease_match(symptoms, min_confidence)
            
            matches = []
            for row in response.data:
                matches.append(DiseaseMatch(
                    disease_id=UUID(row["disease_id"]),
                    disease_name=row["disease_name"],
                    confidence=row["confidence"],
                    matched_symptoms=row["matched_symptoms"],
                    total_symptoms=row["total_symptoms"],
                ))
            
            if not matches:
                logger.info("ℹ️ RPC produced no usable matches, falling back to manual match")
                return self.manual_disease_match(symptoms, min_confidence)
            
            logger.info(f"✅ Found {len(matches)} disease matches via RPC")
            return matches
            
        except Exception as e:
            logger.error(f"❌ Error matching diseases (RPC path): {e}")
            return self.manual_disease_match(symptoms, min_confidence)

    def manual_disease_match(self, symptoms: List[str], min_confidence: float = 0.3) -> List[DiseaseMatch]:
        """Manual disease matching (fallback)"""
        try:
            # Normalize symptoms for consistency
            symptoms = [s.lower().strip() for s in symptoms]
            logger.info(f"🔎 Manual matching for symptoms: {symptoms} (min_conf={min_confidence})")
            
            # Get all diseases
            diseases_response = self.client.table("diseases").select("*").execute()
            matches = []
            
            for disease in diseases_response.data:
                disease_id = disease["disease_id"]
                
                # Get symptoms for this disease
                symptoms_response = self.client.table("disease_symptoms") \
                    .select("symptom_name") \
                    .eq("disease_id", disease_id) \
                    .execute()
                
                disease_symptoms = [s["symptom_name"].lower().strip() for s in symptoms_response.data]
                if not disease_symptoms:
                    continue
                
                # Calculate intersection
                matched = [s for s in symptoms if s in disease_symptoms]
                if not matched:
                    continue
                
                confidence = len(matched) / len(disease_symptoms)
                matches.append(DiseaseMatch(
                    disease_id=UUID(disease_id),
                    disease_name=disease["disease_name"],
                    confidence=confidence,
                    matched_symptoms=matched,
                    total_symptoms=disease.get("total_symptoms", len(disease_symptoms)),
                ))
            
            # Sort by confidence
            matches.sort(key=lambda x: x.confidence, reverse=True)
            
            if not matches:
                logger.warning("⚠️ No disease matched symptoms in manual matcher")
                return []
            
            # Filter by threshold, but if none pass, still return top 1
            strong_matches = [m for m in matches if m.confidence >= min_confidence]
            if strong_matches:
                logger.info(f"✅ {len(strong_matches)} diseases passed confidence threshold")
                return strong_matches[:5]
            
            logger.warning("⚠️ No disease passed confidence threshold; returning best-effort single match")
            return matches[:1]
            
        except Exception as e:
            logger.error(f"❌ Error in manual disease match: {e}")
            return []

    def get_disease_symptoms(self, disease_id: UUID) -> List[DiseaseSymptom]:
        """FIXED: Get symptoms for specific disease - SOLVES agent4 error"""
        try:
            response = self.client.table('disease_symptoms') \
                .select('symptom_name, importance, clarifying_question') \
                .eq('disease_id', str(disease_id)).execute()
            logger.info(f"✅ Fetched {len(response.data)} symptoms for disease {disease_id}")
            return [DiseaseSymptom(**row) for row in response.data]
        except Exception as e:
            logger.error(f"❌ get_disease_symptoms {disease_id}: {e}")
            return []

    def get_severity_rules(self, disease_id: UUID) -> List[SeverityRule]:
        """Get severity rules for a disease"""
        try:
            response = self.client.table("disease_severity_rules") \
                .select("*") \
                .eq("disease_id", str(disease_id)) \
                .execute()
            return [SeverityRule(**rule) for rule in response.data]
            
        except Exception as e:
            logger.error(f"❌ Error getting severity rules: {e}")
            return []

    #  DOCTOR & APPOINTMENT OPERATIONS 
    
    def get_available_doctors(self, specialization: Optional[str] = None) -> List[DoctorResponse]:
        """Get available doctors"""
        try:
            query = self.client.table("doctors").select("*").eq("is_available", True)
            
            if specialization:
                query = query.eq("specialization", specialization)
            
            response = query.execute()
            return [DoctorResponse(**doctor) for doctor in response.data]
            
        except Exception as e:
            logger.error(f"❌ Error getting doctors: {e}")
            return []

    def create_appointment(self, appointment: AppointmentCreate) -> AppointmentResponse:
        """Create appointment"""
        try:
            appointment_data = appointment.dict()
            appointment_data["patient_id"] = str(appointment_data["patient_id"])
            appointment_data["doctor_id"] = str(appointment_data["doctor_id"])
            appointment_data["session_id"] = str(appointment_data["session_id"])
            
            response = self.client.table("appointments") \
                .insert(appointment_data) \
                .execute()
            logger.info(f"✅ Appointment created")
            return AppointmentResponse(**response.data[0])
            
        except Exception as e:
            logger.error(f"❌ Error creating appointment: {e}")
            raise


# Global instance
supabase_client = SupabaseClient()
