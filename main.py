from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging
import os
import sys
from datetime import datetime

# SETUP

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to Python path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Detect actual project root (go up until we find frontend folder)
project_root = parent_dir
while project_root and not os.path.exists(os.path.join(project_root, 'frontend', 'templates')):
    new_root = os.path.dirname(project_root)
    if new_root == project_root:  # Reached filesystem root
        break
    project_root = new_root

logger.info(f"✅ Setup complete - Project root: {project_root}")


# FASTAPI APP

app = FastAPI(
    title='CuraBot API',
    description='Medical AI Chatbot with Multi-Agent System',
    version='2.0.0'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

logger.info("✅ FastAPI app initialized")

# MODELS

class Agent1ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: Optional[str] = None

class Agent1Response(BaseModel):
    user_id: str
    message: str
    response: str
    agent: str = "agent1"
    timestamp: str

class Agent234ChatRequest(BaseModel):
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
    action_type: Optional[str] = None

logger.info("✅ Models defined")

# HELPER FUNCTIONS

def load_html(filename: str) -> str:
    """Load HTML file from templates directory"""
    try:
        # Try multiple possible paths
        possible_paths = [
            os.path.join(project_root, 'frontend', 'templates', filename),
            os.path.join(parent_dir, 'frontend', 'templates', filename),
            os.path.join(os.path.dirname(parent_dir), 'frontend', 'templates', filename),
        ]
        
        for file_path in possible_paths:
            if os.path.exists(file_path):
                logger.info(f"✅ Found HTML: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        
        # If not found, log all attempted paths
        logger.error(f"❌ HTML file '{filename}' not found in any of:")
        for path in possible_paths:
            logger.error(f"   - {path}")
        
        raise FileNotFoundError(f"Could not find {filename}")
        
    except Exception as e:
        logger.error(f"❌ Error loading HTML: {e}")
        raise

# FRONTEND ROUTES

@app.get('/', response_class=HTMLResponse)
async def root():
    """Root page"""
    return HTMLResponse(
        content="""
        <html>
            <head>
                <title>CuraBot</title>
                <style>
                    body { font-family: Arial; padding: 50px; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                    h1 { font-size: 3em; margin-bottom: 20px; }
                    .links { margin-top: 30px; }
                    a { margin: 10px; padding: 15px 30px; background: white; color: #667eea; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: bold; }
                    a:hover { transform: scale(1.05); box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
                </style>
            </head>
            <body>
                <h1>🩺 CuraBot</h1>
                <p>Medical AI Assistant</p>
                <div class="links">
                    <a href="/login">Login</a>
                    <a href="/agent1">Agent 1 - General Health</a>
                    <a href="/agent2">Agent 2 - Symptom Triage</a>
                    <a href="/docs">API Docs</a>
                </div>
            </body>
        </html>
        """
    )

@app.get('/login', response_class=HTMLResponse)
async def login_page():
    """Serve login page"""
    try:
        content = load_html('login.html')
        return HTMLResponse(content=content)
    except Exception as e:
        logger.error(f"Error loading login.html: {e}")
        return HTMLResponse(
            content="<h1>Login page not found</h1><p>Please check frontend/templates/login.html</p>",
            status_code=404
        )

@app.get('/dashboard', response_class=HTMLResponse)
async def dashboard_page():
    """Serve dashboard page"""
    try:
        content = load_html('dashboard.html')
        return HTMLResponse(content=content)
    except Exception as e:
        logger.error(f"Error loading dashboard.html: {e}")
        return HTMLResponse(
            content="<h1>Dashboard not found</h1>",
            status_code=404
        )

@app.get('/agent1', response_class=HTMLResponse)
async def agent1_page():
    """Serve Agent 1 page"""
    try:
        content = load_html('agent1.html')
        return HTMLResponse(content=content)
    except Exception as e:
        logger.error(f"Error loading agent1.html: {e}")
        return HTMLResponse(
            content="<h1>Agent 1 page not found</h1>",
            status_code=404
        )

@app.get('/agent2', response_class=HTMLResponse)
async def agent2_page():
    """Serve Agent 2 page"""
    try:
        content = load_html('agent2.html')
        return HTMLResponse(content=content)
    except Exception as e:
        logger.error(f"Error loading agent2.html: {e}")
        return HTMLResponse(
            content="<h1>Agent 2 page not found</h1>",
            status_code=404
        )

logger.info("✅ Frontend routes registered")

# API ENDPOINTS - AGENT 1

@app.post('/agent1/chat', response_model=dict)
async def agent1_chat(request: Agent1ChatRequest):
    """Agent 1: General Health Query (UNCHANGED)"""
    try:
        logger.info(f"🩺 Agent 1 request: {request.message[:50]}...")
        
        from agents.agent1_general import run_agent1
        
        response = run_agent1(request.message, request.session_id)
        
        return {
            "user_id": request.user_id,
            "message": request.message,
            "response": response,
            "agent": "agent1",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Agent 1 error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

logger.info("✅ Agent 1 endpoint registered")

# API ENDPOINTS - AGENT 2/3/4

@app.post('/agent234/chat', response_model=ChatResponse)
async def agent234_chat(request: Agent234ChatRequest):
    """Agent 2/3/4: Symptom Triage, Disease Matching, Appointment Booking (NEW)"""
    
    logger.info("="*50)
    logger.info("🔬 AGENT 234 ENDPOINT HIT!")
    logger.info(f"📥 Request: {request.message[:50]}...")
    logger.info(f"📞 Phone: {request.phone}")
    logger.info(f"👤 User: {request.user_name}")
    logger.info("="*50)
    
    try:
        # Import orchestrator and models
        from agents.orchestrator import orchestrator
        from database.models import ChatRequest as DBChatRequest
        
        logger.info("✅ Imports successful")
        
        # Convert to internal model
        chat_request = DBChatRequest(
            message=request.message,
            session_id=request.session_id,
            phone=request.phone,
            user_name=request.user_name
        )
        
        logger.info("✅ Request converted")
        
        # Process with orchestrator
        logger.info("🔄 Processing with orchestrator...")
        response = orchestrator.process(chat_request)
        
        logger.info(f"✅ Response: {response.response[:50]}...")
        
        return response
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}", exc_info=True)
        return ChatResponse(
            response="System configuration error. Please contact support.",
            session_id=request.session_id or "error",
            requires_action=False
        )
    
    except Exception as e:
        logger.error(f"❌ Agent 234 error: {e}", exc_info=True)
        return ChatResponse(
            response="I'm having technical difficulties. Please try again.",
            session_id=request.session_id or "error",
            requires_action=False
        )

logger.info("✅ Agent 234 endpoint registered")

# APPOINTMENT ENDPOINTS (AGENT 3)

@app.post('/agent3/book')
async def book_appointment(
    session_id: str,
    doctor_id: str,
    appointment_date: str,
    phone: str
):
    """Book appointment"""
    try:
        from agents.agent3_appointment import agent3
        from database.supabase_client import supabase_client
        from database.models import AgentState
        
        logger.info(f"📅 Booking appointment for session {session_id}")
        
        patient = supabase_client.get_or_create_patient(phone=phone)
        session = supabase_client.get_active_session(patient.patient_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        state = AgentState(
            query="",
            session_id=str(session.session_id),
            patient_id=patient.patient_id,
            phone=phone,
            symptoms_collected=session.symptoms_collected or [],
            disease_identified=session.disease_identified,
            severity_level=session.severity_level,
            severity_score=session.severity_score
        )
        
        appointment_datetime = datetime.fromisoformat(appointment_date)
        response_text = agent3.book_appointment(state, doctor_id, appointment_datetime)
        
        return {"success": True, "message": response_text}
        
    except Exception as e:
        logger.error(f"❌ Booking error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/appointments/list/{phone}')
async def get_appointments(phone: str):
    """Get user's appointments"""
    try:
        from database.supabase_client import supabase_client
        
        patient = supabase_client.get_or_create_patient(phone=phone)
        appointments = supabase_client.get_patient_appointments(patient.patient_id)
        
        appointments_list = []
        for apt in appointments:
            appointments_list.append({
                "appointment_id": str(apt.appointment_id),
                "doctor_id": str(apt.doctor_id),
                "appointment_date": apt.appointment_date.isoformat(),
                "severity_level": apt.severity_level,
                "status": apt.status,
                "emergency_booking": apt.emergency_booking,
                "created_at": apt.created_at.isoformat()
            })
        
        return {"appointments": appointments_list}
        
    except Exception as e:
        logger.error(f"❌ Error fetching appointments: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

logger.info("✅ Appointment endpoints registered")

# HEALTH CHECK

@app.get('/health')
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent1": "operational",
        "agent234": "operational",
        "database": "connected",
        "project_root": project_root
    }

logger.info("✅ Health check registered")

# STARTUP EVENT

@app.on_event("startup")
async def startup_event():
    """Log all registered routes on startup"""
    logger.info("="*70)
    logger.info("🚀 CURABOT API STARTING UP")
    logger.info("="*70)
    logger.info(f"📂 Project Root: {project_root}")
    logger.info("📋 REGISTERED ROUTES:")
    logger.info("="*70)
    
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            logger.info(f"  {methods:8s} {route.path}")
    
    logger.info("="*70)
    logger.info("✅ All routes registered successfully")
    logger.info("="*70)

# RUN SERVER

if __name__ == '__main__':
    import uvicorn
    
    print("\n" + "="*70)
    print(" 🩺 CuraBot API v2.0")
    print("="*70)
    print(f"\n 📂 Base Directory: {project_root}")
    print("\n 📡 API Endpoints:")
    print("    Agent 1:      POST /agent1/chat")
    print("    Agent 234:    POST /agent234/chat")
    print("    Book Apt:     POST /agent3/book")
    print("    Get Apts:     GET  /appointments/list/{phone}")
    print("\n 🌐 Web Pages:")
    print("    Login:        GET  /login")
    print("    Dashboard:    GET  /dashboard")
    print("    Agent 1:      GET  /agent1")
    print("    Agent 2:      GET  /agent2")
    print("\n 🔗 Links:")
    print("    Home:         http://localhost:8000")
    print("    API Docs:     http://localhost:8000/docs")
    print("    Health:       http://localhost:8000/health")
    print("\n" + "="*70 + "\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
