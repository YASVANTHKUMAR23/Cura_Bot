import logging
from typing import Dict, Any
from uuid import UUID
from database.supabase_client import supabase_client
from database.models import AgentState, ChatRequest, ChatResponse as APIChatResponse
from agents.agent2_symptom_triage import agent2
from agents.agent3_appointment import agent3
from agents.agent4_disease_matcher import agent4

logger = logging.getLogger(__name__)

class Orchestrator:
    
    def __init__(self):
        self.agent2 = agent2
        self.agent3 = agent3
        self.agent4 = agent4
        logger.info("✅ Orchestrator initialized")
    
    def process(self, request: ChatRequest) -> APIChatResponse:
        """Main orchestration function"""
        try:
            logger.info(f"🔄 Orchestrator received: {request.message[:50]}...")
            
            # Step 1: Get or create patient
            patient = supabase_client.get_or_create_patient(
                phone=request.phone,
                name=request.user_name
            )
            
            # Step 2: Get or create session
            session = supabase_client.get_active_session(patient.patient_id)
            
            if not session:
                session = supabase_client.create_session(patient.patient_id)
                logger.info(f"✅ New session created: {session.session_id}")
            else:
                logger.info(f"📂 Continuing session: {session.session_id}")
            
            # Step 3: Build agent state
            state = AgentState(
                query=request.message,
                session_id=str(session.session_id),
                patient_id=patient.patient_id,
                phone=request.phone,
                symptoms_collected=session.symptoms_collected or {},
                symptom_count=len(session.symptoms_collected or {}),
                disease_identified=session.disease_identified,
                confidence_score=session.confidence_score,
                severity_level=session.severity_level,
                severity_score=session.severity_score,
                emergency_call_requested=session.emergency_call_requested
            )
            
            # Step 4: Safety check
            state = self._safety_check(state)
            
            if state.safety_status == "UNSAFE":
                return APIChatResponse(
                    response=state.response,
                    session_id=str(session.session_id),
                    requires_action=False
                )
            
            # Step 5: Check if emergency keywords
            if self.agent4.check_emergency_keywords(request.message):
                state.emergency_call_requested = True
                logger.warning("🚨 Emergency call requested by user")
            
            # Step 6: Route through agents
            state = self._route_agents(state)
            
            # Step 7: Build response
            response = APIChatResponse(
                response=state.response,
                session_id=str(session.session_id),
                severity_level=state.severity_level,
                disease_suggested=state.disease_identified,
                confidence=state.confidence_score,
                requires_action=state.requires_action,
                action_type=state.action_type
            )
            
            logger.info(f"✅ Orchestrator completed")
            return response
            
        except Exception as e:
            logger.error(f"❌ Orchestrator error: {e}")
            return APIChatResponse(
                response="I'm having technical difficulties. Please try again in a moment.",
                session_id=request.session_id or "error",
                requires_action=False
            )
    
    def _safety_check(self, state: AgentState) -> AgentState:
        """Check for harmful content"""
        query_lower = state.query.lower()
        
        harmful_keywords = [
            "kill myself",
            "suicide",
            "end my life",
            "want to die"
        ]
        
        if any(kw in query_lower for kw in harmful_keywords):
            state.safety_status = "UNSAFE"
            state.response = """⚠️ I'm concerned about your safety.

Please reach out for immediate help:

🆘 National Suicide Prevention Helpline
   📞 9152987821

🆘 Sneha India (24/7)
   📞 044-24640050

🆘 Vandrevala Foundation
   📞 1860-2662-345

You're not alone. These trained counselors can help."""
            
            logger.warning("🚨 Harmful content detected")
        
        return state
    
    def _route_agents(self, state: AgentState) -> AgentState:
        """Route through Agent 2, 4, 3 workflow"""
        
        # Stage 1: Agent 2 - Extract and collect symptoms
        state = self.agent2.process(state)
        
        if state.needs_more_symptoms:
            # Not enough symptoms, Agent 2 will ask for more
            logger.info("⏸️ Need more symptoms, stopping workflow")
            return state
        
        # Stage 2: Agent 4 - Match diseases
        state = self.agent4.process(state)
        
        # Check if we need to ask clarifying questions
        if state.clarifying_questions and state.current_question_index < len(state.clarifying_questions):
            # Agent 4 generated questions, Agent 2 will ask them
            question = self.agent2.ask_clarifying_questions(
                state, 
                state.clarifying_questions
            )
            
            if question:
                state.response = question
                logger.info("❓ Asking clarifying question")
                return state
        
        # Stage 3: All symptoms collected, disease identified, severity calculated
        if state.disease_identified and state.severity_level:
            # Generate response from Agent 2
            state.response = self.agent2.generate_response(state)
            
            # Stage 4: Agent 3 - Determine action based on severity
            state = self.agent3.process(state)
            
            logger.info(f"✅ Workflow complete: {state.severity_level} severity")
        
        return state


# Global instance
orchestrator = Orchestrator()
