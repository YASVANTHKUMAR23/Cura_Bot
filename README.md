# CuraBot: Industrial-Grade Autonomous Symptom Triage & Healthcare Agent

## 🏥 Overview

**CuraBot** is an **agentic AI healthcare system** designed specifically for **rural and semi-urban India**.

Unlike traditional chatbots, CuraBot uses a **multi-agent autonomous architecture** to:

- Collect and analyze symptoms
- Perform medical triage
- Match diseases using a medical database
- Assess urgency levels
- Coordinate next actions (appointments or emergency alerts)

Built with an **Industrial-First mindset**, the system emphasizes:
- Safety guardrails
- Persistent patient memory
- Retrieval-Augmented Generation (RAG)
- Deterministic workflows

All medical reasoning is grounded in **PubMed-backed knowledge**.


## 🚀 Key Features

### 🧠 Multi-Agent Orchestration
- **Agent 1 – General (RAG)**  
  Handles FAQs and medical questions using **ChromaDB + PubMed**.

- **Agent 2 – Symptom Triage**  
  Collects structured symptoms using the **SOCRATES protocol**.

- **Agent 3 – Action & Urgency**  
  Determines severity, books appointments, or escalates emergencies.

- **Agent 4 – Diagnosis Engine**  
  Matches symptoms to diseases with **confidence scoring**.



### ⚡ Real-Time Disease Matching
- Automatically triggered when **2+ key symptoms** are detected  
  (e.g., fever + headache).
- Uses **Supabase RPC + Vector Search**
- Sub-second diagnosis matching.



### 🛡️ Safety Guardrails
- Immediate intervention for emergency keywords:
  - `suicide`
  - `chest pain`
  - `breathing difficulty`
- Mandatory medical disclaimers for all outputs
- Hard stops for unsafe flows.



### 🧾 Persistent Memory
- Tracks:
  - Patient history
  - Active sessions
  - Previous symptoms
- Backed by **Supabase PostgreSQL**.



## 🏗️ System Architecture

```mermaid
graph TD
    User[User Input] --> API[FastAPI Endpoint]
    API --> Orch[Orchestrator]
    Orch --> Safety[Safety & Emergency Check]
    
    Safety -- Unsafe --> Alert[Emergency Response]
    Safety -- Safe --> Router{Intent Router}
    
    Router -- General Query --> A1[Agent 1: RAG / General]
    Router -- Symptoms --> A2[Agent 2: Triage]
    
    A2 -- Collected Symptoms --> DB[(Supabase Logs)]
    DB --> Logic{Threshold Check}
    
    Logic -- Enough Data --> A4[Agent 4: Disease Matcher]
    Logic -- Need More --> A2
    
    A4 --> A3[Agent 3: Urgency & Booking]
    A3 --> Output[Final Response]


| Layer          | Technology                      |
| -------------- | ------------------------------- |
| Orchestration  | LangGraph                       |
| LLM            | Ollama (Llama 3.2 / OpenBioLLM) |
| Backend        | FastAPI                         |
| Database       | Supabase (PostgreSQL + Vector)  |
| Knowledge Base | ChromaDB (PubMed RAG)           |
| Validation     | Pydantic                        |

📂 Project Structure

D:/CuraBot/
├── agents/
│   ├── orchestrator.py           # Main workflow controller
│   ├── agent1_general.py         # RAG for general queries
│   ├── agent2_symptom_triage.py  # Symptom collection (SOCRATES)
│   ├── agent3_appointment.py     # Urgency & booking
│   └── agent4_disease_matcher.py # Diagnosis logic
│
├── database/
│   ├── supabase_client.py        # RPC & DB helpers
│   ├── models.py                 # Pydantic models
│   └── schema.sql                # Patients, Symptoms, Diseases
│
├── knowledge_base/
│   └── chroma_db/                # Vector store (PubMed)
│
└── api/
    └── main.py                   # FastAPI routes

⚡ Setup & Run
1️⃣ Prerequisites

Python 3.10+

Ollama running locally

ollama serve


Supabase account (Free tier works)

2️⃣ Installation
git clone https://github.com/yourusername/curabot.git
cd curabot
pip install -r requirements.txt

3️⃣ Environment Configuration

Create a .env file in the root directory:

SUPABASE_URL="your_supabase_url"
SUPABASE_KEY="your_supabase_anon_key"
OLLAMA_MODEL="llama3.2"

4️⃣ Run the API
uvicorn api.main:app --reload

5️⃣ Test the API

POST http://localhost:8000/agent234/chat

{
  "message": "High fever, headache, body ache",
  "phone": "+919876543210"

}
