import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Cura_Bot.database.supabase_client import db
from Cura_Bot.utils.logger import setup_logger

logger = setup_logger("seed_supabase")


# Sample disease data
DISEASES_DATA = [
    {
        "name": "Common Cold",
        "symptoms": ["runny nose", "sneezing", "sore throat", "cough", "mild fever"],
        "severity": "mild",
        "category": "respiratory",
        "description": "Viral infection affecting the upper respiratory tract",
        "treatment": "Rest, fluids, over-the-counter medications",
        "prevention": "Hand washing, avoiding close contact with infected people"
    },
    {
        "name": "Influenza (Flu)",
        "symptoms": ["high fever", "body aches", "fatigue", "cough", "headache"],
        "severity": "moderate",
        "category": "respiratory",
        "description": "Contagious respiratory illness caused by influenza viruses",
        "treatment": "Antiviral medications, rest, fluids",
        "prevention": "Annual flu vaccine, good hygiene"
    },
    {
        "name": "Diabetes Type 2",
        "symptoms": ["increased thirst", "frequent urination", "fatigue", "blurred vision", "slow healing"],
        "severity": "chronic",
        "category": "metabolic",
        "description": "Chronic condition affecting blood sugar regulation",
        "treatment": "Lifestyle changes, medication, insulin therapy",
        "prevention": "Healthy diet, regular exercise, weight management"
    },
    {
        "name": "Hypertension",
        "symptoms": ["headaches", "shortness of breath", "nosebleeds", "chest pain"],
        "severity": "moderate",
        "category": "cardiovascular",
        "description": "High blood pressure condition",
        "treatment": "Medication, lifestyle modifications, diet changes",
        "prevention": "Low sodium diet, exercise, stress management"
    },
    {
        "name": "Migraine",
        "symptoms": ["severe headache", "nausea", "sensitivity to light", "visual disturbances"],
        "severity": "moderate",
        "category": "neurological",
        "description": "Recurring severe headache disorder",
        "treatment": "Pain relievers, triptans, preventive medications",
        "prevention": "Identify triggers, maintain routine, stress management"
    },
    {
        "name": "Gastritis",
        "symptoms": ["stomach pain", "nausea", "vomiting", "bloating", "loss of appetite"],
        "severity": "moderate",
        "category": "digestive",
        "description": "Inflammation of the stomach lining",
        "treatment": "Antacids, proton pump inhibitors, dietary changes",
        "prevention": "Avoid irritants, eat smaller meals, reduce stress"
    },
    {
        "name": "Asthma",
        "symptoms": ["wheezing", "shortness of breath", "chest tightness", "coughing"],
        "severity": "moderate",
        "category": "respiratory",
        "description": "Chronic inflammatory disease of the airways",
        "treatment": "Inhalers, corticosteroids, avoiding triggers",
        "prevention": "Identify triggers, maintain medication, regular checkups"
    },
    {
        "name": "Dengue Fever",
        "symptoms": ["high fever", "severe headache", "pain behind eyes", "joint pain", "rash"],
        "severity": "severe",
        "category": "infectious",
        "description": "Mosquito-borne viral infection common in tropical areas",
        "treatment": "Rest, fluids, pain relievers (avoid aspirin)",
        "prevention": "Mosquito control, protective clothing, repellents"
    }
]

# Sample FAQ data
FAQ_DATA = [
    {
        "question": "What is diabetes?",
        "answer": "Diabetes is a chronic condition where the body cannot properly process blood sugar (glucose). Type 1 is autoimmune, while Type 2 is related to lifestyle and genetics.",
        "category": "chronic_diseases"
    },
    {
        "question": "How can I prevent dengue fever?",
        "answer": "Prevent dengue by eliminating mosquito breeding sites, using mosquito repellent, wearing protective clothing, and using mosquito nets. Keep surroundings clean and dry.",
        "category": "infectious_diseases"
    },
    {
        "question": "What should I do if I have high fever?",
        "answer": "For high fever (above 102°F/39°C): Rest, drink plenty of fluids, take acetaminophen or ibuprofen, use cool compresses. Seek medical attention if fever persists for more than 3 days.",
        "category": "symptoms"
    },
    {
        "question": "When should I see a doctor for a cough?",
        "answer": "See a doctor if your cough lasts more than 3 weeks, produces blood, is accompanied by high fever, causes breathing difficulty, or if you have underlying health conditions.",
        "category": "symptoms"
    },
    {
        "question": "What are the symptoms of heart attack?",
        "answer": "Chest pain/discomfort, shortness of breath, pain in arms/jaw/neck/back, cold sweats, nausea, lightheadedness. Call emergency services immediately if you suspect a heart attack.",
        "category": "emergency"
    },
    {
        "question": "How to manage high blood pressure?",
        "answer": "Manage BP through: low-sodium diet, regular exercise, maintaining healthy weight, limiting alcohol, reducing stress, taking prescribed medications, and regular monitoring.",
        "category": "chronic_diseases"
    }
]


def seed_diseases():
    """Seed disease data into Supabase"""
    logger.info("Seeding disease data...")
    
    try:
        for disease in DISEASES_DATA:
            disease['created_at'] = datetime.utcnow().isoformat()
            
        result = db.supabase.table("diseases").upsert(DISEASES_DATA).execute()
        logger.info(f"✅ Seeded {len(DISEASES_DATA)} diseases")
        return True
    except Exception as e:
        logger.error(f"Error seeding diseases: {e}")
        return False


def seed_faqs():
    """Seed FAQ data into Supabase"""
    logger.info("Seeding FAQ data...")
    
    try:
        for faq in FAQ_DATA:
            faq['created_at'] = datetime.utcnow().isoformat()
            
        result = db.supabase.table("faqs").upsert(FAQ_DATA).execute()
        logger.info(f"✅ Seeded {len(FAQ_DATA)} FAQs")
        return True
    except Exception as e:
        logger.error(f"Error seeding FAQs: {e}")
        return False


def create_sample_patient():
    """Create a sample patient record for testing"""
    logger.info("Creating sample patient...")
    
    sample_patient = {
        "user_id": "sample_patient_001",
        "phone_number": "+919876543210",
        "name": "Test User",
        "age": 30,
        "gender": "other",
        "location": "Mumbai, India",
        "created_at": datetime.utcnow().isoformat()
    }
    
    try:
        result = db.supabase.table("patients").upsert(sample_patient).execute()
        logger.info("✅ Sample patient created")
        return True
    except Exception as e:
        logger.error(f"Error creating sample patient: {e}")
        return False


def verify_seeding():
    """Verify that data was seeded correctly"""
    logger.info("Verifying seeded data...")
    
    try:
        # Check diseases
        diseases = db.supabase.table("diseases").select("*").execute()
        logger.info(f"Found {len(diseases.data)} diseases in database")
        
        # Check FAQs
        faqs = db.supabase.table("faqs").select("*").execute()
        logger.info(f"Found {len(faqs.data)} FAQs in database")
        
        # Check patients
        patients = db.supabase.table("patients").select("*").execute()
        logger.info(f"Found {len(patients.data)} patients in database")
        
        return True
    except Exception as e:
        logger.error(f"Error verifying data: {e}")
        return False


def seed_all():
    """Run all seeding operations"""
    print("🌱 Starting database seeding...\n")
    
    # Seed diseases
    if seed_diseases():
        print("✅ Diseases seeded successfully")
    else:
        print("❌ Failed to seed diseases")
    
    # Seed FAQs
    if seed_faqs():
        print("✅ FAQs seeded successfully")
    else:
        print("❌ Failed to seed FAQs")
    
    # Create sample patient
    if create_sample_patient():
        print("✅ Sample patient created")
    else:
        print("❌ Failed to create sample patient")
    
    # Verify
    print("\n🔍 Verifying seeded data...")
    if verify_seeding():
        print("\n🎉 Database seeding completed successfully!")
    else:
        print("\n⚠️  Seeding verification failed")


if __name__ == "__main__":
    seed_all()
