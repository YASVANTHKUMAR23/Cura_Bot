import logging
from typing import Dict, List, Any, Optional
from uuid import UUID
from database.supabase_client import supabase_client
from database.models import AgentState, SymptomLog
from utils.llm_client_v2 import llm_client

logger = logging.getLogger(__name__)

class Agent2SymptomTriage:
    
    def __init__(self):
        self.min_symptoms_required = 3
        logger.info("✅ Agent 2: Symptom Triage initialized")
    
    def extract_symptoms(self, query: str) -> List[str]:
        """Extract symptoms from user message using LLM"""
        try:
            prompt = f"""
Extract ONLY the medical symptoms from this user message. Return as comma-separated list.

Examples:
User: "I have high fever and headache"
Output: fever, headache

User: "I'm feeling very tired and have body ache"
Output: extreme_tiredness, body_ache

User: "my gums are bleeding"
Output: bleeding_gums

Common symptom names to use:
- fever, headache, body_ache, cough, cold, sore_throat
- nausea, vomiting, diarrhea, stomach_pain
- rash, bleeding_gums, bleeding_nose
- chest_pain, shortness_of_breath, difficulty_breathing
- extreme_tiredness, dizziness, weakness
- joint_pain, muscle_pain

User message: "{query}"

Symptoms (comma-separated):"""
            
            response = llm_client.generate(prompt, temperature=0.1)
            
            # Parse response
            symptoms_text = response.strip().lower()
            symptoms = [s.strip() for s in symptoms_text.split(",") if s.strip()]
            
            # Normalize symptom names
            symptoms = self._normalize_symptoms(symptoms)
            
            logger.info(f"🔍 Extracted symptoms: {symptoms}")
            return symptoms
            
        except Exception as e:
            logger.error(f"❌ Error extracting symptoms: {e}")
            return []
    
    def _normalize_symptoms(self, symptoms: List[str]) -> List[str]:
        """Normalize symptom names to database format"""
        normalization_map = {
            "high fever": "fever",
            "temperature": "fever",
            "head ache": "headache",
            "body pain": "body_ache",
            "muscle ache": "body_ache",
            "tired": "extreme_tiredness",
            "fatigue": "extreme_tiredness",
            "skin rash": "rash",
            "stomach ache": "stomach_pain",
            "abdominal pain": "stomach_pain",
        }
        
        normalized = []
        for symptom in symptoms:
            normalized.append(normalization_map.get(symptom, symptom))
        
        return list(set(normalized))  # Remove duplicates
    
    def process(self, state: AgentState) -> AgentState:
        """Main processing function for Agent 2"""
        try:
            logger.info(f"🔄 Agent 2 processing: {state.query}")
            
            # Extract symptoms from current query
            new_symptoms = self.extract_symptoms(state.query)
            
            # Update state with new symptoms
            for symptom in new_symptoms:
                if symptom not in state.symptoms_collected:
                    state.symptoms_collected[symptom] = {
                        "detected": True,
                        "severity": None,
                        "duration": None
                    }
                    state.symptom_count += 1
                    
                    # Log to database
                    try:
                        supabase_client.log_symptom(SymptomLog(
                            session_id=UUID(state.session_id),
                            symptom_name=symptom
                        ))
                    except Exception as e:
                        logger.error(f"Error logging symptom: {e}")
            
            # Check if we have enough symptoms
            if state.symptom_count < self.min_symptoms_required:
                state.needs_more_symptoms = True
                state.response = self._ask_for_more_symptoms(state)
                return state
            
            # We have enough symptoms - mark for Agent 4
            state.needs_more_symptoms = False
            logger.info(f"✅ Collected {state.symptom_count} symptoms, ready for Agent 4")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Agent 2 error: {e}")
            state.response = "I'm having trouble understanding. Could you describe your symptoms again?"
            return state
    
    def _ask_for_more_symptoms(self, state: AgentState) -> str:
        """Generate response asking for more symptoms"""
        symptoms_so_far = list(state.symptoms_collected.keys())
        
        prompt = f"""
You are a medical assistant collecting symptoms. The user has mentioned: {', '.join(symptoms_so_far)}.

You need at least {self.min_symptoms_required} symptoms but only have {state.symptom_count}.

Generate a friendly response that:
1. Acknowledges their symptoms
2. Asks them to mention 2-3 more symptoms from this list:
   - Body ache or joint pain
   - Cough or cold
   - Nausea or vomiting
   - Rash on skin
   - Extreme tiredness
   - Sore throat
   - Dizziness
   - Stomach pain

Keep it conversational and empathetic. Don't sound robotic.

Response:"""
        
        try:
            response = llm_client.generate(prompt, temperature=0.7)
            return response.strip()
        except:
            # Fallback response
            return f"""I understand you have {', '.join(symptoms_so_far)}.

To help you accurately, please tell me if you have any of these:
• Body ache or joint pain
• Cough or cold
• Nausea or vomiting
• Rash on skin
• Extreme tiredness
• Sore throat

Which of these are you experiencing?"""
    
    def ask_clarifying_questions(self, state: AgentState, questions: List[str]) -> str:
        """Ask clarifying questions from Agent 4"""
        if not questions:
            return ""
        
        # Get next question to ask
        if state.current_question_index < len(questions):
            question = questions[state.current_question_index]
            state.current_question_index += 1
            
            logger.info(f"❓ Asking clarifying question: {question}")
            return question
        
        return ""
    
    def generate_response(self, state: AgentState) -> str:
        """Generate final response based on disease identification"""
        try:
            if not state.disease_identified or not state.confidence_score:
                return "I'm analyzing your symptoms. Please wait..."
            
            disease = state.disease_identified
            confidence = state.confidence_score
            severity = state.severity_level or "unknown"
            
            # Build response with DISCLAIMER
            prompt = f"""
Generate a medical triage response with these details:

Disease Suggested: {disease}
Confidence: {confidence:.0%}
Severity: {severity}
Other Possibilities: {', '.join([d.disease_name for d in state.possible_diseases[1:3]]) if len(state.possible_diseases) > 1 else 'None'}

CRITICAL RULES:
1. NEVER say "You have {disease}" - always say "symptoms SUGGEST" or "might be"
2. Include clear disclaimer that only doctor can confirm
3. Be empathetic and helpful
4. If severity is high/moderate, recommend doctor visit
5. If severity is low, provide self-care tips

Generate response:"""
            
            response = llm_client.generate(prompt, temperature=0.7)
            return response.strip()
            
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}")
            return "I've analyzed your symptoms. Please consult a doctor for proper diagnosis."


# Global instance
agent2 = Agent2SymptomTriage()
