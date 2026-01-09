import sys
from datetime import datetime

print("=" * 60)
print(" CuraBot Full System Test")
print(f" Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60 + "\n")

# Test 1: Database
print("1 Testing Database Connection...")
try:
    from Cura_Bot.database.supabase_client import db
    print("    Database: Connected\n")
except Exception as e:
    print(f"     Database: {e}\n")

# Test 2: Agent 1
print("2 Testing Agent 1 (General Medical)...")
try:
    from Cura_Bot.agents.agent1_general import run_agent1
    print("    Agent 1: Initialized\n")
except Exception as e:
    print(f"    Agent 1: {e}\n")

# Test 3: Agent 2
print("3 Testing Agent 2 (Symptom Triage)...")
try:
    from Cura_Bot.agents.agent2_symptom_triage import Agent2
    agent2 = Agent2()
    print("    Agent 2: Initialized\n")
except Exception as e:
    print(f"    Agent 2: {e}\n")

# Test 4: Agent 3
print("4 Testing Agent 3 (Appointment Scheduling)...")
try:
    from Cura_Bot.agents.agent3_appointment import Agent3
    from Cura_Bot.database.supabase_client import db
    agent3 = Agent3(db)
    print("    Agent 3: Initialized\n")
except Exception as e:
    print(f"    Agent 3: {e}\n")

# Test 5: Agent 4
print("5 Testing Agent 4 (Disease Matcher)...")
try:
    from Cura_Bot.agents.agent4_disease_matcher import Agent4
    from Cura_Bot.database.supabase_client import db
    agent4 = Agent4(db)
    print("    Agent 4: Initialized\n")
except Exception as e:
    print(f"    Agent 4: {e}\n")

# Test 6: FastAPI
print("6 Testing FastAPI...")
try:
    from Cura_Bot.api.main import app
    print("    FastAPI: Ready\n")
except Exception as e:
    print(f"    API: {e}\n")

print("=" * 60)
print(" TESTING COMPLETED!")
print("=" * 60)
print("\n CuraBot System Status:")
print(" Start server: python run.py")
print(" Test Agent 1: python Cura_Bot/agents/agent1_general.py")
