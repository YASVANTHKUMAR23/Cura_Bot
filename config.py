import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# === PROJECT PATHS ===
PROJECT_ROOT = Path(__file__).parent.absolute()
CHROMA_DB_PATH = PROJECT_ROOT / 'knowledge_base' / 'chroma_db'
GUARDRAILS_PATH = PROJECT_ROOT / 'guardrials'  # Note: your typo preserved
LOGS_PATH = PROJECT_ROOT / 'logs'
LOGS_PATH.mkdir(exist_ok=True)

# Verify paths
if CHROMA_DB_PATH.exists():
    print(f'✅ ChromaDB found: {CHROMA_DB_PATH}')
else:
    print(f'⚠️ WARNING: ChromaDB not found: {CHROMA_DB_PATH}')

# === SUPABASE CONFIGURATION ===
SUPABASE_URL = os.getenv('SUPABASE_URL', 'PASTE_YOUR_SUPABASE_URL_HERE')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'PASTE_YOUR_SUPABASE_KEY_HERE')

# === OLLAMA CONFIGURATION ===
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
OLLAMA_TEMPERATURE = float(os.getenv('OLLAMA_TEMPERATURE', '0.3'))

# === AGENT CONFIGURATION ===
AGENT_CONFIG = {
    'session_timeout_minutes': 10,
    'max_conversation_history': 20,
    'agent4_confidence_threshold': {
        'high': 0.75,
        'moderate': 0.60,
        'low': 0.0
    },
    'emergency_cancellation_window_seconds': 10
}

# === DISEASE DETECTION (20 Topics for PMC) ===
DISEASE_TOPICS = [
    'Heart Attack', 'Stroke', 'Diabetes', 'Hypertension', 'Asthma',
    'Dengue', 'Malaria', 'Typhoid', 'Tuberculosis', 'Pneumonia',
    'COVID-19', 'Common Cold', 'Influenza', 'Migraine', 'GERD',
    'Appendicitis', 'Kidney Stones', 'UTI', 'Anemia', 'Thyroid Disorders'
]

# Disease risk levels
DISEASE_RISK_LEVELS = {
    'CRITICAL_RISK': ['Heart Attack', 'Stroke', 'Severe Allergic Reaction', 'Sepsis'],
    'HIGH_RISK': ['Dengue', 'Malaria', 'Typhoid', 'Appendicitis', 'Pneumonia', 'COVID-19'],
    'MODERATE_RISK': ['Diabetes', 'Hypertension', 'Asthma', 'Tuberculosis'],
    'LOW_RISK': ['Common Cold', 'Influenza', 'Migraine', 'GERD', 'UTI']
}

# === SEVERITY MATRIX ===
SEVERITY_MATRIX = {
    ('CRITICAL_RISK', 'MILD'): 'HIGH',
    ('CRITICAL_RISK', 'MODERATE'): 'CRITICAL',
    ('CRITICAL_RISK', 'SEVERE'): 'CRITICAL',
    ('CRITICAL_RISK', 'CRITICAL'): 'CRITICAL',
    
    ('HIGH_RISK', 'MILD'): 'MODERATE',
    ('HIGH_RISK', 'MODERATE'): 'HIGH',
    ('HIGH_RISK', 'SEVERE'): 'CRITICAL',
    ('HIGH_RISK', 'CRITICAL'): 'CRITICAL',
    
    ('MODERATE_RISK', 'MILD'): 'MILD',
    ('MODERATE_RISK', 'MODERATE'): 'MODERATE',
    ('MODERATE_RISK', 'SEVERE'): 'HIGH',
    ('MODERATE_RISK', 'CRITICAL'): 'CRITICAL',
    
    ('LOW_RISK', 'MILD'): 'MILD',
    ('LOW_RISK', 'MODERATE'): 'MILD',
    ('LOW_RISK', 'SEVERE'): 'MODERATE',
    ('LOW_RISK', 'CRITICAL'): 'HIGH',
}

# === RED FLAGS ===
RED_FLAG_KEYWORDS = [
    'chest pain', 'heart attack', 'crushing chest',
    'can\'t breathe', 'difficulty breathing', 'choking',
    'stroke', 'paralysis', 'facial drooping', 'slurred speech',
    'seizure', 'unconscious', 'fainted',
    'vomiting blood', 'coughing blood', 'severe bleeding',
    'anaphylaxis', 'swelling throat'
]

# === LOGGING ===
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# === PMC INGESTION ===
PMC_CONFIG = {
    'articles_per_topic': 2,
    'chunk_size': 500,
    'chunk_overlap': 50,
    'max_article_length': 50000
}

print(f'✅ Config loaded: Model={OLLAMA_MODEL}')

