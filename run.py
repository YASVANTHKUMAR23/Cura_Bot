import subprocess
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_ollama():
    
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        if response.status_code == 200:
            logger.info('✅ Ollama is running')
            return True
    except:
        logger.error('❌ Ollama is not running')
        logger.info('Please start Ollama: ollama serve')
        return False


def check_supabase():
    
    from config import SUPABASE_URL, SUPABASE_KEY
    
    if 'your-project' in SUPABASE_URL:
        logger.error('❌ Supabase not configured')
        logger.info('Please update .env with your Supabase credentials')
        return False
    
    logger.info('✅ Supabase configured')
    return True


def check_chromadb():
    
    if Path('knowledge_base/chroma_db').exists():
        logger.info('✅ ChromaDB found')
        return True
    else:
        logger.warning('⚠️  ChromaDB not found. Run: python data_ingestion/ingest_diseases_pmc.py')
        return False


def main():
    logger.info('=== CuraBot Startup Checks ===\\n')
    
    checks = {
        'Ollama': check_ollama(),
        'Supabase': check_supabase(),
        'ChromaDB': check_chromadb()
    }
    
    if not all(checks.values()):
        logger.error('\\n❌ Startup checks failed. Please fix errors above.')
        sys.exit(1)
    
    logger.info('\\n✅ All checks passed!\\n')
    logger.info('Choose an option:')
    logger.info('1. Run demo scenarios')
    logger.info('2. Start FastAPI server')
    logger.info('3. Run tests')
    
    choice = input('\\nEnter choice (1-3): ')
    
    if choice == '1':
        logger.info('\\nRunning demo scenarios...\\n')
        subprocess.run([sys.executable, 'demo/demo_scenarios.py'])
    
    elif choice == '2':
        logger.info('\\nStarting FastAPI server...\\n')
        subprocess.run([sys.executable, 'api/main.py'])
    
    elif choice == '3':
        logger.info('\\nRunning tests...\\n')
        subprocess.run([sys.executable, '-m', 'pytest', 'demo/test_cases.py', '-v'])


if __name__ == '__main__':
    main()
