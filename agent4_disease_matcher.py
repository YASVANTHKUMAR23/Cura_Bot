import logging
from typing import Dict, List, Any, Optional
from uuid import UUID
from database.supabase_client import supabase_client
from database.models import DiseaseMatch, DiseaseSymptom

logger = logging.getLogger(__name__)

class Agent4DiseaseMatcher:
    def __init__(self):
        self.min_confidence = 0.6
        logger.info("✅ Agent 4 Disease Matcher initialized")

    def process(self, state) -> Any:
        """Main disease matching process"""
        try:
            logger.info("🔍 Agent 4: Starting disease matching...")
            
            # Check emergency first
            if self.check_emergency_keywords(state.message):
                state.severity_level = "CRITICAL"
                state.requires_action = True
                state.action_type = "emergency_call"
                logger.warning("🚨 EMERGENCY KEYWORDS DETECTED")
                return state
            
            # Get current symptoms from session
            session_symptoms = supabase_client.get_session_symptoms(state.session.session_id)
            current_symptoms = [s.symptom_name.lower() for s in session_symptoms if s.severity != "unknown"]
            
            if not current_symptoms:
                logger.info("ℹ️ No symptoms collected yet")
                state.clarifying_questions = ["Could you describe your symptoms?"]
                return state
            
            # Match diseases
            matches = self.match_diseases(current_symptoms)
            state.disease_matches = matches
            
            if matches:
                top_match = max(matches, key=lambda x: x.confidence)
                state.disease_suggested = top_match.disease_name
                state.confidence = top_match.confidence
                state.severity_level = self.calculate_severity(top_match.disease_id)
                logger.info(f"✅ Top match: {top_match.disease_name} ({top_match.confidence:.2f})")
                
                if top_match.confidence >= self.min_confidence:
                    state.disease_identified = True
                else:
                    state.clarifying_questions = self.generate_clarifying_questions(current_symptoms, matches)
            else:
                logger.info("❌ No disease matches found")
                state.clarifying_questions = ["Can you provide more details about your symptoms?"]
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Agent4 process error: {e}")
            state.response = "Sorry, having trouble matching symptoms. Please describe more."
            return state

    def check_emergency_keywords(self, message: str) -> bool:
        """Check for emergency keywords"""
        emergency_keywords = [
            'chest pain', 'difficulty breathing', 'severe pain', 'unconscious', 
            'bleeding heavily', 'seizure', 'heart attack', 'stroke', 'cannot breathe'
        ]
        return any(keyword in message.lower() for keyword in emergency_keywords)

    def match_diseases(self, symptoms: List[str]) -> List[DiseaseMatch]:
        """Match symptoms to diseases from DB"""
        all_diseases = supabase_client.get_all_diseases()
        matches = []
        
        for disease in all_diseases:
            disease_symptoms = supabase_client.get_disease_symptoms(disease.id)
            symptom_list = [s.symptom_name.lower() for s in disease_symptoms]
            matching_symptoms = len(set(symptoms) & set(symptom_list))
            total_symptoms = len(symptom_list)
            
            if matching_symptoms > 0:
                confidence = matching_symptoms / max(total_symptoms, 1)
                matches.append(DiseaseMatch(
                    disease_name=disease.name,
                    disease_id=disease.id,
                    confidence=confidence,
                    matching_count=matching_symptoms
                ))
        
        return sorted(matches, key=lambda x: x.confidence, reverse=True)

    # Add other methods: calculate_severity, generate_clarifying_questions if missing
    def calculate_severity(self, disease_id: UUID) -> str:
        rules = supabase_client.get_disease_severity_rules(disease_id)
        return rules[0].severity_level if rules else "low"

    def generate_clarifying_questions(self, symptoms: List[str], matches: List[DiseaseMatch]) -> List[str]:
        return ["Any other symptoms like fever, cough, or nausea?"]

agent4 = Agent4DiseaseMatcher()
