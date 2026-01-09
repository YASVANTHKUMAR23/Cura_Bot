-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Patients Table
CREATE TABLE IF NOT EXISTS patients (
    patient_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100),
    age INTEGER,
    gender VARCHAR(10),
    location VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. Conversation Sessions Table
CREATE TABLE IF NOT EXISTS conversation_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(patient_id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'active',
    symptoms_collected JSONB DEFAULT '{}',
    disease_identified VARCHAR(100),
    confidence_score FLOAT,
    severity_level VARCHAR(20),
    severity_score INTEGER,
    emergency_call_requested BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- 3. Symptoms Log Table
CREATE TABLE IF NOT EXISTS symptoms_log (
    symptom_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES conversation_sessions(session_id) ON DELETE CASCADE,
    symptom_name VARCHAR(100) NOT NULL,
    severity VARCHAR(20),
    duration VARCHAR(50),
    additional_details JSONB,
    detected_at TIMESTAMP DEFAULT NOW()
);

-- 4. Diseases Master Table
CREATE TABLE IF NOT EXISTS diseases (
    disease_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    disease_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    total_symptoms INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 5. Disease Symptoms Master Table
CREATE TABLE IF NOT EXISTS disease_symptoms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    disease_id UUID REFERENCES diseases(disease_id) ON DELETE CASCADE,
    symptom_name VARCHAR(100) NOT NULL,
    importance VARCHAR(20) DEFAULT 'MEDIUM',
    clarifying_question TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(disease_id, symptom_name)
);

-- 6. Disease Severity Rules
CREATE TABLE IF NOT EXISTS disease_severity_rules (
    rule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    disease_id UUID REFERENCES diseases(disease_id) ON DELETE CASCADE,
    symptom_name VARCHAR(100) NOT NULL,
    severity_level VARCHAR(20),
    weight_points INTEGER DEFAULT 0,
    emergency_criteria TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 7. Doctors Table
CREATE TABLE IF NOT EXISTS doctors (
    doctor_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    specialty VARCHAR(100),
    location VARCHAR(200),
    available BOOLEAN DEFAULT true,
    phone VARCHAR(20),
    rating FLOAT DEFAULT 4.5,
    next_available_slot TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 8. Appointments Table
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id UUID REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    session_id UUID REFERENCES conversation_sessions(session_id) ON DELETE CASCADE,
    appointment_date TIMESTAMP NOT NULL,
    severity_level VARCHAR(20),
    status VARCHAR(20) DEFAULT 'pending',
    summary TEXT,
    emergency_booking BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 9. Doctor-Patient Chats
CREATE TABLE IF NOT EXISTS doctor_patient_chats (
    chat_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    appointment_id UUID REFERENCES appointments(appointment_id) ON DELETE CASCADE,
    sender VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT NOW()
);

-- Create Indexes
CREATE INDEX IF NOT EXISTS idx_sessions_patient ON conversation_sessions(patient_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON conversation_sessions(status);
CREATE INDEX IF NOT EXISTS idx_symptoms_session ON symptoms_log(session_id);
CREATE INDEX IF NOT EXISTS idx_disease_symptoms ON disease_symptoms(disease_id, symptom_name);
CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_chats_appointment ON doctor_patient_chats(appointment_id);

-- Insert Mock Doctors
INSERT INTO doctors (name, specialty, location, available, phone, rating, next_available_slot) VALUES
('Dr. Rajesh Kumar', 'General Physician', 'Chennai, Tamil Nadu', true, '+91-9876543210', 4.8, NOW() + INTERVAL '5 hours'),
('Dr. Priya Sharma', 'Cardiologist', 'Chennai, Tamil Nadu', true, '+91-9876543211', 4.9, NOW() + INTERVAL '2 hours'),
('Dr. Anand Menon', 'Diabetologist', 'Coimbatore, Tamil Nadu', true, '+91-9876543212', 4.7, NOW() + INTERVAL '1 day'),
('Dr. Lakshmi Iyer', 'General Physician', 'Mettupalayam, Tamil Nadu', true, '+91-9876543213', 4.6, NOW() + INTERVAL '8 hours'),
('Dr. Suresh Reddy', 'Infectious Disease', 'Chennai, Tamil Nadu', true, '+91-9876543214', 4.8, NOW() + INTERVAL '3 hours')
ON CONFLICT DO NOTHING;

-- Insert Sample Diseases
INSERT INTO diseases (disease_name, description, total_symptoms) VALUES
('Dengue Fever', 'Mosquito-borne viral infection', 10),
('Chikungunya', 'Viral disease transmitted by mosquitoes', 8),
('Typhoid', 'Bacterial infection', 9),
('Viral Fever', 'Common viral infection', 6),
('Malaria', 'Parasitic disease transmitted by mosquitoes', 8),
('Diabetes', 'Metabolic disorder affecting blood sugar', 7),
('Heart Attack', 'Cardiac emergency', 10)
ON CONFLICT DO NOTHING;

-- Insert Dengue Symptoms
INSERT INTO disease_symptoms (disease_id, symptom_name, importance, clarifying_question)
SELECT disease_id, 'fever', 'HIGH', 'What is your current body temperature?' FROM diseases WHERE disease_name = 'Dengue Fever'
UNION ALL
SELECT disease_id, 'headache', 'MEDIUM', 'How severe is your headache on scale 1-10?' FROM diseases WHERE disease_name = 'Dengue Fever'
UNION ALL
SELECT disease_id, 'body_ache', 'HIGH', 'Do you have severe muscle or body pain?' FROM diseases WHERE disease_name = 'Dengue Fever'
UNION ALL
SELECT disease_id, 'rash', 'HIGH', 'Do you have any skin rash?' FROM diseases WHERE disease_name = 'Dengue Fever'
UNION ALL
SELECT disease_id, 'extreme_tiredness', 'MEDIUM', 'Are you experiencing extreme fatigue?' FROM diseases WHERE disease_name = 'Dengue Fever'
UNION ALL
SELECT disease_id, 'bleeding_gums', 'HIGH', 'Have you noticed any bleeding from gums or nose?' FROM diseases WHERE disease_name = 'Dengue Fever'
UNION ALL
SELECT disease_id, 'severe_abdominal_pain', 'HIGH', 'Do you have severe stomach pain?' FROM diseases WHERE disease_name = 'Dengue Fever'
UNION ALL
SELECT disease_id, 'persistent_vomiting', 'HIGH', 'Are you vomiting repeatedly?' FROM diseases WHERE disease_name = 'Dengue Fever'
UNION ALL
SELECT disease_id, 'difficulty_breathing', 'HIGH', 'Do you have difficulty breathing?' FROM diseases WHERE disease_name = 'Dengue Fever'
UNION ALL
SELECT disease_id, 'nausea', 'MEDIUM', 'Do you feel nauseous?' FROM diseases WHERE disease_name = 'Dengue Fever'
ON CONFLICT DO NOTHING;

-- Insert Dengue Severity Rules
INSERT INTO disease_severity_rules (disease_id, symptom_name, severity_level, weight_points, emergency_criteria)
SELECT disease_id, 'fever', 'moderate', 10, 'Fever > 102°F for 4+ days' FROM diseases WHERE disease_name = 'Dengue Fever'
UNION ALL
SELECT disease_id, 'bleeding_gums', 'high', 30, 'Any bleeding is warning sign' FROM diseases WHERE disease_name = 'Dengue Fever'
UNION ALL
SELECT disease_id, 'severe_abdominal_pain', 'high', 25, 'Severe pain indicates complications' FROM diseases WHERE disease_name = 'Dengue Fever'
UNION ALL
SELECT disease_id, 'persistent_vomiting', 'high', 25, 'Cannot retain fluids' FROM diseases WHERE disease_name = 'Dengue Fever'
UNION ALL
SELECT disease_id, 'difficulty_breathing', 'high', 30, 'Respiratory distress' FROM diseases WHERE disease_name = 'Dengue Fever'
UNION ALL
SELECT disease_id, 'body_ache', 'moderate', 10, 'Severe body pain common' FROM diseases WHERE disease_name = 'Dengue Fever'
UNION ALL
SELECT disease_id, 'rash', 'moderate', 10, 'Dengue rash' FROM diseases WHERE disease_name = 'Dengue Fever'
UNION ALL
SELECT disease_id, 'extreme_tiredness', 'low', 5, 'Common symptom' FROM diseases WHERE disease_name = 'Dengue Fever'
ON CONFLICT DO NOTHING;

-- Insert Heart Attack Symptoms
INSERT INTO disease_symptoms (disease_id, symptom_name, importance, clarifying_question)
SELECT disease_id, 'chest_pain', 'HIGH', 'Where exactly is the chest pain located?' FROM diseases WHERE disease_name = 'Heart Attack'
UNION ALL
SELECT disease_id, 'pain_radiation', 'HIGH', 'Is the pain spreading to your arm, jaw, or back?' FROM diseases WHERE disease_name = 'Heart Attack'
UNION ALL
SELECT disease_id, 'shortness_of_breath', 'HIGH', 'Are you having difficulty breathing?' FROM diseases WHERE disease_name = 'Heart Attack'
UNION ALL
SELECT disease_id, 'sweating', 'HIGH', 'Are you sweating profusely?' FROM diseases WHERE disease_name = 'Heart Attack'
UNION ALL
SELECT disease_id, 'nausea', 'MEDIUM', 'Do you feel nauseous or dizzy?' FROM diseases WHERE disease_name = 'Heart Attack'
ON CONFLICT DO NOTHING;

-- Insert Heart Attack Severity Rules
INSERT INTO disease_severity_rules (disease_id, symptom_name, severity_level, weight_points, emergency_criteria)
SELECT disease_id, 'chest_pain', 'high', 25, 'Central chest pain' FROM diseases WHERE disease_name = 'Heart Attack'
UNION ALL
SELECT disease_id, 'pain_radiation', 'high', 30, 'Radiation to left arm/jaw' FROM diseases WHERE disease_name = 'Heart Attack'
UNION ALL
SELECT disease_id, 'shortness_of_breath', 'high', 25, 'Difficulty breathing' FROM diseases WHERE disease_name = 'Heart Attack'
UNION ALL
SELECT disease_id, 'sweating', 'high', 20, 'Cold sweats' FROM diseases WHERE disease_name = 'Heart Attack'
ON CONFLICT DO NOTHING;

-- Grant permissions (adjust as needed)
-- ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE conversation_sessions ENABLE ROW LEVEL SECURITY;
-- etc...

COMMIT;
