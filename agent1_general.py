import operator
from typing import Annotated, List, TypedDict, Dict
from datetime import datetime
import logging
import os

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

import chromadb
from chromadb.utils import embedding_functions

# Import NeMo Guardrails
from nemoguardrails import LLMRails, RailsConfig

# CONFIGURATION 
DB_PATH = "./knowledge_base/chroma_db"
GUARDRAILS_PATH = "Cura_Bot/guardrails"
LLM_MODEL = "llama3.2:3b"

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent1_logs.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Agent1")


#  1. LOAD GUARDRAILS 
def load_guardrails():
    """Load NeMo Guardrails"""
    try:
        if not os.path.exists(GUARDRAILS_PATH):
            logger.warning("Guardrails not found - using fallback")
            return None
        
        config = RailsConfig.from_path(GUARDRAILS_PATH)
        rails = LLMRails(config)
        logger.info(" NeMo Guardrails loaded")
        return rails
    except Exception as e:
        logger.error(f"Guardrails error: {e}")
        return None

guardrails = load_guardrails()


#  2. STATE DEFINITION 
class AgentState(TypedDict):
    query: str
    session_id: str
    chat_history: Annotated[List[BaseMessage], operator.add]
    context: str
    source_list: List[str]
    answer: str
    safety_status: str
    confidence_score: float
    has_rag_data: bool
    has_symptoms: bool  # NEW: Detect if user mentions symptoms


#  3. SESSION MANAGER 
class SessionManager:
    def __init__(self):
        self.sessions = {}
    
    def get_history(self, session_id: str) -> List[BaseMessage]:
        if session_id not in self.sessions:
            self.sessions[session_id] = {"history": [], "context": ""}
        return self.sessions[session_id]["history"]
    
    def add_message(self, session_id: str, message: BaseMessage):
        if session_id not in self.sessions:
            self.sessions[session_id] = {"history": [], "context": ""}
        self.sessions[session_id]["history"].append(message)
        # Keep last 10 messages
        if len(self.sessions[session_id]["history"]) > 10:
            self.sessions[session_id]["history"] = self.sessions[session_id]["history"][-10:]

session_manager = SessionManager()


# 4. DATABASE CONNECTION 
def get_medical_db():
    """Connect to ChromaDB"""
    try:
        client = chromadb.PersistentClient(path=DB_PATH)
        embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        return client.get_collection(name="medical_knowledge", embedding_function=embed_fn)
    except Exception as e:
        logger.error(f"ChromaDB error: {e}")
        return None

collection = get_medical_db()
llm = ChatOllama(model=LLM_MODEL, temperature=0.3)


#  5. SYMPTOM DETECTION 
def detect_symptoms(query: str) -> bool:
    """
    Detect if user is describing personal symptoms
    Returns True if symptoms detected
    """
    # Personal symptom indicators
    personal_indicators = [
        "i have", "i am having", "i feel", "i'm feeling",
        "my", "i've been", "experiencing", "suffering from"
    ]
    
    # Symptom keywords
    symptom_keywords = [
        "pain", "headache", "fever", "cough", "vomit", "nausea",
        "diarrhea", "bleeding", "rash", "swelling", "dizzy", "tired",
        "weak", "chest pain", "shortness of breath", "difficulty breathing",
        "stomach ache", "sore throat", "runny nose", "body ache"
    ]
    
    query_lower = query.lower()
    
    # Check if personal + symptom
    has_personal = any(ind in query_lower for ind in personal_indicators)
    has_symptom = any(symp in query_lower for symp in symptom_keywords)
    
    return has_personal and has_symptom


#  6. NODE FUNCTIONS 

def guardrail_router(state: AgentState):
    """
    Step 1: SAFETY CHECK using NeMo Guardrails
    Falls back to manual checks if NeMo is unavailable
    """
    query = state["query"]
    session_id = state.get("session_id", "default")
    
    #  USE NEMO GUARDRAILS IF AVAILABLE 
    if guardrails is not None:
        try:
            logger.info(f"🛡️ Running NeMo Guardrails check for: {query}")
            
            # Run guardrails check
            result = guardrails.generate(messages=[{
                "role": "user",
                "content": query
            }])
            
            # Get response
            response_text = result.get('content', '').lower()
            
            logger.info(f"🛡️ NeMo response: {response_text[:100]}")
            
            # Check if NeMo blocked it
            blocked_phrases = [
                "i can only discuss health",
                "focus only on medical",
                "medical ai assistant"
            ]
            
            is_blocked = any(phrase in response_text for phrase in blocked_phrases)
            
            if is_blocked:
                logger.warning(f"🚫 NeMo Guardrails blocked: {query}")
                return {
                    "safety_status": "NON_MEDICAL",
                    "query": query,
                    "has_symptoms": False
                }
            
            # Query passed NeMo Guardrails
            logger.info(f"✅ NeMo Guardrails passed: {query}")
            return {
                "safety_status": "SAFE",
                "query": query,
                "has_symptoms": detect_symptoms(query)
            }
            
        except Exception as e:
            logger.error(f"NeMo Guardrails error: {e}")
            logger.warning("Falling back to manual checks")
            # Fall through to manual checks
    
    #  FALLBACK: MANUAL CHECKS 
    logger.info("Using manual safety checks (NeMo not available)")
    
    query_lower = query.lower()
    
    # Check 1: Harmful content
    harmful_keywords = [
        "kill myself", "suicide", "self harm", "overdose",
        "how to die", "end my life"
    ]
    
    if any(kw in query_lower for kw in harmful_keywords):
        logger.warning(f"🚫 Harmful query detected: {query}")
        return {
            "safety_status": "UNSAFE",
            "query": query,
            "has_symptoms": False
        }
    
    # Check 2: Allow greetings
    greetings = ["hello", "hi", "hey", "good morning", "good evening"]
    if any(greet in query_lower for greet in greetings):
        logger.info(f"✅ Greeting detected: {query}")
        return {
            "safety_status": "SAFE",
            "query": query,
            "has_symptoms": False
        }
    
    # Check 3: Medical relevance
    medical_keywords = [
        "health", "medical", "disease", "symptom", "pain", "fever",
        "medicine", "medication", "doctor", "treatment", "diabetes",
        "aspirin", "drug", "tablet", "hospital", "illness"
    ]
    
    has_medical = any(kw in query_lower for kw in medical_keywords)
    
    if not has_medical:
        # Check for obvious off-topic
        off_topic = ["messi", "cricket", "movie", "stock", "politics"]
        if any(ot in query_lower for ot in off_topic):
            logger.info(f"🚫 Off-topic query: {query}")
            return {
                "safety_status": "NON_MEDICAL",
                "query": query,
                "has_symptoms": False
            }
    
    # Default: ALLOW
    logger.info(f"✅ Query passed manual checks: {query}")
    return {
        "safety_status": "SAFE",
        "query": query,
        "has_symptoms": detect_symptoms(query)
    }

def retrieve_knowledge(state: AgentState):
    """Step 2: RAG RETRIEVAL"""
    if state["safety_status"] != "SAFE":
        return {"context": "", "source_list": [], "confidence_score": 0.0, "has_rag_data": False}
    
    if not collection:
        logger.warning("ChromaDB not available")
        return {"context": "", "source_list": [], "confidence_score": 0.0, "has_rag_data": False}
    
    logger.info(f" Retrieving docs for: {state['query']}")
    
    try:
        results = collection.query(
            query_texts=[state["query"]],
            n_results=3,
            include=['documents', 'metadatas', 'distances']
        )
        
        if not results['documents'][0]:
            return {"context": "", "source_list": [], "confidence_score": 0.0, "has_rag_data": False}
        
        distances = results.get('distances', [[1.0]])[0]
        
        # Low relevance threshold
        if distances[0] > 0.8:
            logger.info(f" Low relevance, using LLM knowledge")
            return {"context": "", "source_list": [], "confidence_score": 0.0, "has_rag_data": False}
        
        # Calculate confidence
        avg_distance = sum(distances) / len(distances)
        confidence = 1.0 / (1.0 + avg_distance)
        
        # Build context
        context_text = ""
        sources = []
        
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            context_text += f"\n--- SOURCE {i+1} ---\n{doc}\n"
            title = meta.get('title', meta.get('Title', 'Medical Study'))
            sources.append(f"{title} (PMC)")
        
        logger.info(f" Retrieved {len(sources)} sources (Confidence: {confidence:.0%})")
        
        return {
            "context": context_text,
            "source_list": sources,
            "confidence_score": confidence,
            "has_rag_data": True
        }
    
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return {"context": "", "source_list": [], "confidence_score": 0.0, "has_rag_data": False}


def generate_answer(state: AgentState):
    """Step 3: ANSWER GENERATION with Symptom Detection"""
    status = state["safety_status"]
    has_rag = state.get("has_rag_data", False)
    confidence = state.get("confidence_score", 0.0)
    has_symptoms = state.get("has_symptoms", False)
    
    # Handle blocked queries
    if status == "UNSAFE":
        return {"answer": " I'm concerned about your safety. Please contact:\n\n National Suicide Prevention Helpline: 9152987821\n Sneha India: 044-24640050"}
    
    if status == "NON_MEDICAL":
        return {"answer": " I'm a medical health assistant and can only answer health-related questions.\n\n I can help with:\n Disease information\n Medications and treatments\n Preventive care\n Wellness advice\n\n How can I help with your health?"}
    
    # Generate answer
    if has_rag and state.get("context"):
        # RAG Answer
        prompt = ChatPromptTemplate.from_template("""
You are a Medical Information Assistant with verified medical literature.

GUIDELINES:
1. Answer using the CONTEXT below as primary source
2. Use simple, clear language
3. Do NOT diagnose or prescribe
4. Provide general information only

VERIFIED CONTEXT:
{context}

USER QUESTION:
{query}

ANSWER:
""")
        
        chain = prompt | llm | StrOutputParser()
        
        try:
            response = chain.invoke({"context": state["context"], "query": state["query"]})
            
            confidence_emoji = "" if confidence > 0.7 else "" if confidence > 0.4 else ""
            sources = state.get("source_list", [])
            
            final_answer = f"{response}\n\n{confidence_emoji} **Source: Verified Medical Literature** (Confidence: {confidence:.0%})"
            
            if sources:
                final_answer += f"\n\n **References:**\n" + "\n".join([f" {s}" for s in sources])
            
            #  NEW: Add symptom detection suggestion
            if has_symptoms:
                final_answer += "\n\n---\n\n **I noticed you mentioned personal symptoms.** For personalized symptom analysis and health recommendations, I suggest using our **Symptom Triage Agent** which can:\n Analyze your symptoms in detail\n Assess urgency levels\n Provide personalized next steps\n\n Would you like to switch to the Symptom Triage Agent?"
            
            return {"answer": final_answer}
        
        except Exception as e:
            logger.error(f"Generation error: {e}")
            has_rag = False
    
    # LLM General Knowledge
    if not has_rag:
        prompt = ChatPromptTemplate.from_template("""
You are a Medical Information Assistant providing general health information.

RULES:
1. Provide general medical information only
2. Use simple language
3. NEVER diagnose or prescribe
4. Recommend consulting healthcare provider for personal symptoms

USER QUESTION:
{query}

ANSWER:
""")
        
        chain = prompt | llm | StrOutputParser()
        
        try:
            response = chain.invoke({"query": state["query"]})
            
            disclaimer = "\n\n **Note:** General information only. Consult a healthcare provider for your specific situation."
            final_answer = f"{response}{disclaimer}\n\n **Source: General Medical Knowledge**"
            
            #  NEW: Add symptom detection suggestion
            if has_symptoms:
                final_answer += "\n\n---\n\n **I noticed you mentioned personal symptoms.** For personalized symptom analysis and health recommendations, I suggest using our **Symptom Triage Agent** which can:\n Analyze your symptoms in detail\n Assess urgency levels\n Provide personalized next steps\n\n Would you like to switch to the Symptom Triage Agent?"
            
            return {"answer": final_answer}
        
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return {"answer": " Error generating response. Please try again."}


#  7. BUILD THE GRAPH 
workflow = StateGraph(AgentState)

workflow.add_node("guardrail", guardrail_router)
workflow.add_node("retrieve", retrieve_knowledge)
workflow.add_node("generate", generate_answer)

workflow.set_entry_point("guardrail")

def route_check(state):
    if state["safety_status"] in ["UNSAFE", "NON_MEDICAL"]:
        return "generate"
    return "retrieve"

workflow.add_conditional_edges(
    "guardrail",
    route_check,
    {"retrieve": "retrieve", "generate": "generate"}
)

workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

agent1_app = workflow.compile()


#  8. PUBLIC INTERFACE 
def run_agent1(user_query: str, session_id: str = "default"):
    """Main function to run Agent 1"""
    start_time = datetime.now()
    
    history = session_manager.get_history(session_id)
    
    inputs = {
        "query": user_query,
        "session_id": session_id,
        "chat_history": history,
        "has_rag_data": False,
        "has_symptoms": False
    }
    
    result = agent1_app.invoke(inputs)
    
    # Update session
    session_manager.add_message(session_id, HumanMessage(content=user_query))
    session_manager.add_message(session_id, AIMessage(content=result["answer"]))
    
    response_time = (datetime.now() - start_time).total_seconds()
    logger.info(f" Processed in {response_time:.2f}s")
    
    return result["answer"]


#  9. INTERACTIVE MODE 
def interactive_mode():
    """Chat interface for testing"""
    import uuid
    session_id = str(uuid.uuid4())[:8]
    
    print("\n" + "="*70)
    print(" AGENT 1: GENERAL HEALTH QUERY ASSISTANT")
    print(f" Session: {session_id}")
    print("="*70)
    print("\n Type your health question (or 'exit' to quit)\n")
    print("-"*70)
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("\n Stay healthy!\n")
            break
        
        if not user_input:
            continue
        
        print("\n Agent 1:\n")
        response = run_agent1(user_input, session_id)
        print(response)
        print("\n" + "-"*70)


if __name__ == "__main__":
    interactive_mode()
