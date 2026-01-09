import time
import random
from datetime import datetime, timedelta

def send_message_mock(user_message, session_id="test_123"):
    """
    Simulates the Main Chat API (POST /api/chat).
    Returns a fake response based on keywords in your message.
    """
    
    # Simulate network delay (so Frontend can test "Loading..." spinners)
    time.sleep(1.5)
    
    msg = user_message.lower()
    
    # SCENARIO 1: General Health Question (Agent 1)
    if "diabetes" in msg or "fever" in msg or "food" in msg:
        return {
            "status": "success",
            "agent_active": "Agent 1 (General)",
            "reply_text": "Based on standard medical guidelines, a diet low in refined sugars is recommended for diabetes prevention. [Source: CDC Guidelines]",
            "ui_action": "NONE",
            "data": None
        }

    # SCENARIO 2: Symptom Triage (Agent 2)
    elif "pain" in msg or "headache" in msg:
        return {
            "status": "success",
            "agent_active": "Agent 2 (Triage)",
            "reply_text": "I understand. To help me assess this better, could you tell me on a scale of 1-10 how severe the pain is?",
            "ui_action": "NONE",
            "data": {
                "symptom_detected": "pain",
                "stage": "assessment"
            }
        }

    # SCENARIO 3: Booking Request (Agent 2 Trigger)
    elif "book" in msg or "appointment" in msg:
        return {
            "status": "success",
            "agent_active": "Agent 2 (Booking)",
            "reply_text": "I can help with that. Please select a convenient time slot from the form below.",
            "ui_action": "SHOW_BOOKING_FORM",  # <--- Frontend triggers Modal
            "data": {
                "doctor_name": "Dr. Aravind Patel",
                "specialty": "General Physician"
            }
        }

    # SCENARIO 4: Emergency (Agent 3)
    elif "chest" in msg or "heart" in msg or "dying" in msg:
        return {
            "status": "success",
            "agent_active": "Agent 3 (Urgency)",
            "reply_text": "⚠️ CRITICAL ALERT: Your symptoms indicate a potential medical emergency. I am connecting you to an emergency doctor immediately.",
            "ui_action": "EMERGENCY_ALERT",  # <--- Frontend triggers Red Flash/Siren
            "data": {
                "urgency_level": "CRITICAL",
                "hospital": "City General Hospital"
            }
        }

    # Default Fallback
    else:
        return {
            "status": "success",
            "agent_active": "Router",
            "reply_text": "I'm the Mock AI. I didn't understand that keyword. Try 'diabetes', 'pain', 'book', or 'heart'.",
            "ui_action": "NONE",
            "data": None
        }

def get_booking_slots_mock(doctor_id="dr_001"):
    """
    Simulates fetching available slots (GET /api/slots).
    """
    time.sleep(0.5)
    
    # Generate next 3 days
    today = datetime.now()
    
    return {
        "doctor_id": doctor_id,
        "available_slots": [
            (today + timedelta(days=1)).strftime("%Y-%m-%d 10:00 AM"),
            (today + timedelta(days=1)).strftime("%Y-%m-%d 02:30 PM"),
            (today + timedelta(days=2)).strftime("%Y-%m-%d 11:15 AM"),
        ]
    }
