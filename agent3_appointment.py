import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
from database.supabase_client import supabase_client
from database.models import (
    AgentState, 
    AppointmentCreate, 
    DoctorResponse,
    SessionUpdate
)
from utils.llm_client_v2 import llm_client

logger = logging.getLogger(__name__)

class Agent3Appointment:
    
    def __init__(self):
        logger.info("✅ Agent 3: Appointment Booking initialized")
    
    def process(self, state: AgentState) -> AgentState:
        """Main processing function for Agent 3"""
        try:
            logger.info(f"🔄 Agent 3 processing: Severity={state.severity_level}")
            
            # Check severity level and determine action
            if state.severity_level == "HIGH":
                return self._handle_high_severity(state)
            elif state.severity_level == "MODERATE":
                return self._handle_moderate_severity(state)
            else:  # LOW
                return self._handle_low_severity(state)
            
        except Exception as e:
            logger.error(f"❌ Agent 3 error: {e}")
            state.response = "I'm having trouble processing. Please try again."
            return state
    
    def _handle_high_severity(self, state: AgentState) -> AgentState:
        """Handle HIGH severity - Emergency protocol"""
        logger.warning(f"🚨 HIGH SEVERITY detected for session {state.session_id}")
        
        # Check if user explicitly requested call
        if state.emergency_call_requested:
            # User asked for emergency call
            state.requires_action = True
            state.action_type = "emergency_call"
            
            # Generate doctor summary
            summary = self._generate_doctor_summary(state)
            
            # Find available doctor
            doctors = supabase_client.get_available_doctors(
                specialty="General Physician"
            )
            
            if doctors:
                # Create emergency appointment
                appointment = self._create_emergency_appointment(
                    state, 
                    doctors[0], 
                    summary
                )
                
                response = f"""🚨 EMERGENCY DETECTED

I'm connecting you to a doctor immediately.
This will happen in 10 seconds.

Doctor: {doctors[0].name}
Specialty: {doctors[0].specialty}

[Skip - I'll go to hospital myself]
[Continue - Connect me now]

Countdown: 10... 9... 8..."""
                
            else:
                # No doctor available - urgent appointment
                response = f"""🚨 CRITICAL SITUATION

No doctor is immediately available for live call.

RECOMMENDED ACTION:
• Visit nearest hospital emergency room
• OR Call emergency helpline: 108

I can book an urgent appointment for callback within 5 minutes.

[Book Urgent Appointment] [I'll go to hospital]"""
            
            state.response = response
            
        else:
            # High severity but user didn't ask for call
            # Just recommend urgent appointment
            state.requires_action = True
            state.action_type = "urgent_appointment"
            
            summary = self._generate_doctor_summary(state)
            
            response = f"""⚠️ URGENT: Your symptoms indicate a serious condition.

Based on your symptoms:
• Disease: {state.disease_identified}
• Severity: HIGH
• Score: {state.severity_score}/150

🏥 IMMEDIATE ACTION NEEDED:
I strongly recommend seeing a doctor urgently.

Would you like me to:
1. Book urgent appointment (within 2 hours)
2. Connect you to a doctor now (if you need immediate help)

Please choose an option."""
            
            state.response = response
        
        # Update session
        try:
            supabase_client.update_session(
                UUID(state.session_id),
                SessionUpdate(
                    severity_level="HIGH",
                    severity_score=state.severity_score,
                    emergency_call_requested=state.emergency_call_requested
                )
            )
        except Exception as e:
            logger.error(f"Error updating session: {e}")
        
        return state
    
    def _handle_moderate_severity(self, state: AgentState) -> AgentState:
        """Handle MODERATE severity - Book appointment"""
        logger.info(f"📅 MODERATE severity - recommending appointment")
        
        state.requires_action = True
        state.action_type = "book_appointment"
        
        # Get available doctors
        doctors = supabase_client.get_available_doctors()
        
        if not doctors:
            state.response = "I recommend seeing a doctor, but I'm having trouble finding available doctors. Please contact your local clinic."
            return state
        
        # Generate response with doctor options
        doctors_list = "\n\n".join([
            f"""👨‍⚕️ {doctor.name}
   {doctor.specialty} | ⭐ {doctor.rating}
   {doctor.location}
   Available: {self._format_slot(doctor.next_available_slot)}
   [Select Doctor {i+1}]"""
            for i, doctor in enumerate(doctors[:3])
        ])
        
        response = f"""Based on your symptoms, I recommend booking an appointment.

📋 Your Symptom Analysis:
• Condition: {state.disease_identified} (likely)
• Other possibilities: {', '.join([d.disease_name for d in state.possible_diseases[1:3]]) if len(state.possible_diseases) > 1 else 'None'}
• Confidence: {state.confidence_score:.0%}
• Severity: MODERATE

⚠️ Note: Only a doctor can confirm the diagnosis through proper examination and tests.

🏥 Available Doctors Near You:

{doctors_list}

Would you like to book an appointment?
[Yes, Book Now] [Show Self-Care Tips First] [I'll Decide Later]"""
        
        state.response = response
        
        # Update session
        try:
            supabase_client.update_session(
                UUID(state.session_id),
                SessionUpdate(
                    status="awaiting_appointment",
                    severity_level="MODERATE",
                    severity_score=state.severity_score
                )
            )
        except Exception as e:
            logger.error(f"Error updating session: {e}")
        
        return state
    
    def _handle_low_severity(self, state: AgentState) -> AgentState:
        """Handle LOW severity - Self-care advice"""
        logger.info(f"💊 LOW severity - providing self-care advice")
        
        state.requires_action = False
        state.action_type = "self_care"
        
        # Generate self-care advice using LLM
        prompt = f"""
Generate self-care advice for a patient with these symptoms:

Disease: {state.disease_identified}
Severity: LOW
Symptoms: {', '.join(state.symptoms_collected.keys())}

Provide:
1. Rest and hydration advice
2. Over-the-counter medication suggestions (generic)
3. Warning signs to watch for
4. When to see a doctor

Keep it friendly and reassuring. Don't diagnose.

Self-care advice:"""
        
        try:
            advice = llm_client.generate(prompt, temperature=0.7)
        except:
            advice = """
✓ Get adequate rest
✓ Stay well hydrated (8-10 glasses of water daily)
✓ Continue any prescribed medications
✓ Monitor your symptoms
✓ Maintain a healthy diet"""
        
        response = f"""Based on your symptoms, you have mild {state.disease_identified}.

{advice}

⚠️ Contact a doctor if:
• Symptoms worsen
• New symptoms appear
• No improvement in 2-3 days

Would you like to:
[Book Follow-up Appointment] [Get More Information] [I'm Done]"""
        
        state.response = response
        
        # Update session
        try:
            supabase_client.update_session(
                UUID(state.session_id),
                SessionUpdate(
                    status="completed",
                    severity_level="LOW",
                    severity_score=state.severity_score,
                    completed_at=datetime.now()
                )
            )
        except Exception as e:
            logger.error(f"Error updating session: {e}")
        
        return state
    
    def _generate_doctor_summary(self, state: AgentState) -> str:
        """Generate summary for doctor"""
        symptoms_list = "\n".join([f"• {symptom}" for symptom in state.symptoms_collected.keys()])
        
        other_diseases = [d.disease_name for d in state.possible_diseases[1:3]] if len(state.possible_diseases) > 1 else []
        
        summary = f"""PATIENT CONSULTATION SUMMARY

Patient ID: {state.patient_id}
Session ID: {state.session_id}
Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}

CHIEF COMPLAINT:
{state.query[:200]}

SYMPTOMS REPORTED:
{symptoms_list}

CLINICAL IMPRESSION (AI Analysis):
Primary: {state.disease_identified} (Confidence: {state.confidence_score:.0%})
Other Possibilities: {', '.join(other_diseases) if other_diseases else 'None'}

SEVERITY ASSESSMENT:
Level: {state.severity_level}
Score: {state.severity_score}/150

RECOMMENDED TESTS:
[To be determined by doctor based on disease]

NOTE: This is AI-assisted triage. Please conduct complete examination and tests for confirmation.
"""
        
        return summary
    
    def _create_emergency_appointment(
        self, 
        state: AgentState, 
        doctor: DoctorResponse,
        summary: str
    ) -> Optional[Any]:
        """Create emergency appointment"""
        try:
            appointment_data = AppointmentCreate(
                patient_id=state.patient_id,
                doctor_id=doctor.doctor_id,
                session_id=UUID(state.session_id),
                appointment_date=datetime.now() + timedelta(minutes=5),
                severity_level="HIGH",
                summary=summary,
                emergency_booking=True
            )
            
            appointment = supabase_client.create_appointment(appointment_data)
            logger.info(f"✅ Emergency appointment created: {appointment.appointment_id}")
            
            return appointment
            
        except Exception as e:
            logger.error(f"❌ Error creating emergency appointment: {e}")
            return None
    
    def book_appointment(
        self, 
        state: AgentState, 
        doctor_id: str,
        appointment_datetime: datetime
    ) -> str:
        """Book regular appointment"""
        try:
            summary = self._generate_doctor_summary(state)
            
            appointment_data = AppointmentCreate(
                patient_id=state.patient_id,
                doctor_id=UUID(doctor_id),
                session_id=UUID(state.session_id),
                appointment_date=appointment_datetime,
                severity_level=state.severity_level or "MODERATE",
                summary=summary,
                emergency_booking=False
            )
            
            appointment = supabase_client.create_appointment(appointment_data)
            
            # Update session
            supabase_client.update_session(
                UUID(state.session_id),
                SessionUpdate(
                    status="appointment_booked",
                    completed_at=datetime.now()
                )
            )
            
            logger.info(f"✅ Appointment booked: {appointment.appointment_id}")
            
            return f"""✅ Appointment Confirmed!

📅 Details:
Date: {appointment_datetime.strftime("%B %d, %Y")}
Time: {appointment_datetime.strftime("%I:%M %P")}
Doctor: [Doctor name from ID]

📝 The doctor has received a detailed summary of your symptoms.

🔔 You'll receive a reminder 30 minutes before.

Take care! 👋"""
            
        except Exception as e:
            logger.error(f"❌ Error booking appointment: {e}")
            return "I'm sorry, there was an error booking the appointment. Please try again."
    
    def _format_slot(self, slot: Optional[datetime]) -> str:
        """Format appointment slot"""
        if not slot:
            return "Contact for availability"
        
        now = datetime.now()
        diff = slot - now
        
        if diff.days == 0:
            return f"Today {slot.strftime('%I:%M %P')}"
        elif diff.days == 1:
            return f"Tomorrow {slot.strftime('%I:%M %P')}"
        else:
            return slot.strftime("%b %d, %I:%M %P")


# Global instance
agent3 = Agent3Appointment()
