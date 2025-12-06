import os
import uvicorn
import google.generativeai as genai
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import certifi
import uuid
from datetime import datetime

# --- IMPORT PRIVACY VAULT ---
try:
    from privacy_vault import vault
except ImportError:
    print("⚠️ Vault not found. Using mock.")
    class MockVault:
        def scrub(self, t): return t
    vault = MockVault()

app = FastAPI()

# --- 1. CONFIGURATION ---
# PASTE YOUR KEY HERE
os.environ["GOOGLE_API_KEY"] = ""
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# 2. MONGODB (Optional - Use your string or leave as is for local testing)
# If you don't have Mongo yet, the app will still run but won't save history.
MONGO_URI = ""

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=3000)
    db = client["nexus_db"]
    chats_collection = db["chats"]
    client.admin.command('ping')
    print("✅ Connected to MongoDB Atlas")
except Exception as e:
    print(f"⚠️ MongoDB Failed: {e}. Running without history.")
    chats_collection = None

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestData(BaseModel):
    text: str
    session_id: str = None
    user_email: str = "anonymous"
    preferred_model: str = "auto"

# --- 2. NEW GEMINI 2.5 SWARM ---
def ask_gemini_swarm(prompt: str):
    """
    Uses your available models: 2.5 Flash for speed, 2.5 Pro for reasoning.
    """
    # 1. Decide which model to use
    if "code" in prompt.lower() or "analyze" in prompt.lower() or "complex" in prompt.lower():
        # Use the Smartest Model you have
        target_model = 'models/gemini-2.5-pro'
    else:
        # Use the Fastest Model you have
        target_model = 'models/gemini-2.5-flash'

    # 2. Try to run it (with fallbacks)
    fallback_models = [
        'models/gemini-2.5-flash', 
        'models/gemini-2.0-flash', 
        'models/gemini-pro'
    ]
    
    # Add target to front of list
    models_to_try = [target_model] + [m for m in fallback_models if m != target_model]

    for model_name in models_to_try:
        try:
            print(f"✨ Routing to {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text, f"Google {model_name.split('/')[-1]}"
        except Exception as e:
            print(f"❌ {model_name} failed: {e}")
            continue

    return "Error: All AI models failed. Check API Key.", "Offline"

@app.post("/analyze")
async def analyze(data: RequestData):
    print(f"\n📥 Input: {data.text[:50]}...")
    
    # 1. PRIVACY SCRUB
    safe_text = vault.scrub(data.text)
    
    # 2. CLOUD INTELLIGENCE
    final_prompt = f"Analyze this redacted data: {safe_text}"
    insight, engine = ask_gemini_swarm(final_prompt)

    # 3. SAVE TO CLOUD
    if chats_collection is not None:
        try:
            session_id = data.session_id or str(uuid.uuid4())
            chat_entry = {
                "session_id": session_id,
                "user_email": data.user_email,
                "user_text": data.text,
                "ai_response": insight,
                "engine": engine,
                "timestamp": datetime.now().isoformat()
            }
            chats_collection.insert_one(chat_entry)
            print("💾 Saved to MongoDB")
        except Exception as e:
            print(f"⚠️ Save Failed: {e}")

    return {
        "original_redacted": safe_text,
        "analysis": insight,
        "engine": engine,
        "session_id": data.session_id or str(uuid.uuid4())
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
