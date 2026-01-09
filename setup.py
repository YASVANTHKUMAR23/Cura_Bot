import subprocess
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def install_dependencies():
    logger.info('Installing dependencies...')
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])


def setup_database():
    logger.info('Setting up database...')
    
    # Read schema
    schema_path = Path('database/schema.sql')
    if schema_path.exists():
        logger.info('✅ Database schema found')
        logger.info('⚠️  Please run schema.sql in your Supabase dashboard')
    else:
        logger.warning('⚠️  schema.sql not found')


def seed_database():
    
    logger.info('Seeding database...')
    
    try:
        from Cura_Bot.knowledge_base.seed_supabase import main as seed_main
        seed_main()
        logger.info('✅ Database seeded')
    except Exception as e:
        logger.error(f'❌ Seeding failed: {e}')


def ingest_medical_knowledge():
    
    logger.info('Ingesting medical knowledge from PMC...')
    logger.info('⚠️  This may take 10-15 minutes...')
    
    try:
        from Cura_Bot.knowledge_base.ingest_pmc_fulltext import main as ingest_main
        ingest_main()
        logger.info('✅ Medical knowledge ingested')
    except Exception as e:
        logger.error(f'❌ Ingestion failed: {e}')


def verify_setup():
    
    logger.info('\\nVerifying setup...')
    
    checks = {
        'Config file': Path('config.py').exists(),
        'Orchestrator': Path('orchestrator.py').exists(),
        'Agent 2': Path('agents/agent2_symptom_triage.py').exists(),
        'Agent 3': Path('agents/agent3_doctor_liaison.py').exists(),
        'Agent 4': Path('agents/agent4_disease_matcher.py').exists(),
        'Database client': Path('database/supabase_client.py').exists(),
        'LLM client': Path('utils/llm_client.py').exists(),
        'ChromaDB': Path('knowledge_base/chroma_db').exists(),
        'Guardrails': Path('guardrials/config.yml').exists(),
    }
    
    for check, status in checks.items():
        icon = '✅' if status else '❌'
        logger.info(f'{icon} {check}')
    
    all_ok = all(checks.values())
    
    if all_ok:
        logger.info('\\n✅ Setup complete! Ready to run.')
    else:
        logger.warning('\\n⚠️  Some components missing. Check errors above.')


def main():
    logger.info('=== CuraBot Setup ===\\n')
    
    # Step 1: Dependencies
    install_dependencies()
    
    # Step 2: Database
    setup_database()
    
    # Step 3: Seed data
    seed_response = input('\\nSeed database with mock hospitals/doctors? (y/n): ')
    if seed_response.lower() == 'y':
        seed_database()
    
    # Step 4: Ingest knowledge
    ingest_response = input('\\nIngest medical knowledge from PMC? (takes 10-15 min) (y/n): ')
    if ingest_response.lower() == 'y':
        ingest_medical_knowledge()
    
    # Step 5: Verify
    verify_setup()
    
    logger.info('\\n=== Next Steps ===')
    logger.info('1. Update .env with your Supabase credentials')
    logger.info('2. Run database/schema.sql in Supabase')
    logger.info('3. Start Ollama: ollama serve')
    logger.info('4. Pull model: ollama pull llama3.2:3b')
    logger.info('5. Run demo: python demo/demo_scenarios.py')
    logger.info('6. Start API: python api/main.py')


if __name__ == '__main__':
    main()
