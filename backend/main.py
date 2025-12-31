# backend/main.py
import os
import uvicorn
import uuid
import certifi
import sys
import pandas as pd
import json
import time
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path

from fastapi import FastAPI, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv
from google import genai

# --- IMPORT MODULES ---
from utils.loaders import load_file_universally
from utils.file_store import MongoFileStore
from agents.vault import VaultAgent
from agents.analyst import AnalystAgent
from agents.translator import TranslatorAgent

# 1. SETUP
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

MONGO_URI = os.getenv("MONGO_URI")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not MONGO_URI or not GOOGLE_API_KEY:
    raise RuntimeError("❌ CRITICAL: Missing MONGO_URI or GOOGLE_API_KEY")

genai_client = genai.Client(api_key=GOOGLE_API_KEY)

try:
    mongo_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = mongo_client["nexus_db"]
    print("✅ Connected to MongoDB Atlas")
except Exception as e:
    print(f"❌ MongoDB Failed: {e}")
    db = None

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# 🟢 ROBUST MODEL ROTATOR (Solves 429 & 404 Errors)
# =========================================================
def generate_content_robust(prompt: str, json_mode: bool = False):
    """
    Tries multiple models. If one fails (Quota/NotFound), it instantly tries the next.
    """
    models_to_try = [
        'gemini-2.5-flash',       # Primary
        'gemini-2.0-flash',       # Fallback 1
        'gemini-flash-latest',    # Fallback 2
        'gemini-1.5-flash',       # Fallback 3
        'gemini-1.5-pro'          # Last Resort
    ]
    
    last_error = None
    
    for model in models_to_try:
        try:
            config = {'response_mime_type': 'application/json'} if json_mode else None
            response = genai_client.models.generate_content(
                model=model, 
                contents=prompt,
                config=config
            )
            return response.text
        except Exception as e:
            error_msg = str(e)
            # Only switch if it's a "Limit" or "Not Found" error
            if "429" in error_msg or "404" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                # print(f"⚠️ {model} failed. Switching...")
                last_error = e
                continue
            else:
                # If it's a real bug, raise it
                raise e
                
    raise RuntimeError(f"All models failed. Last error: {str(last_error)}")

# 2. INITIALIZE AGENTS (Pass the Rotator Function)
file_store = MongoFileStore(db)
vault = VaultAgent(mongo_db=db)
analyst = AnalystAgent(generate_content_robust, vault)
translator = TranslatorAgent(generate_content_robust)

active_sessions: Dict[str, dict] = {} 

class AnalyzeRequest(BaseModel):
    text: str
    session_id: Optional[str] = None
    user_email: str = "anonymous"
    translation_mode: str = "mixed" 

# 3. API ENDPOINTS

@app.post("/upload")
async def upload(file: UploadFile = File(...), user_email: str = Header("anonymous")):
    sid = str(uuid.uuid4())
    try:
        content = await file.read()
        data, dtype = load_file_universally(file.filename, content)
        if data is None: return {"error": "Unsupported file format"}

        if vault and dtype == "structured":
            protected_data = vault.ingest_file(data, session_id=sid)
        else:
            protected_data = data

        file_store.save_file(sid, protected_data, dtype, file.filename)
        active_sessions[sid] = {"data": protected_data, "type": dtype}

        if db is not None:
            ts = datetime.now().isoformat()
            db.sessions.insert_one({"session_id": sid, "user_email": user_email, "title": file.filename, "created_at": ts, "file_attached": True})
            db.messages.insert_one({
                "session_id": sid, "role": "assistant", 
                "content": f"✅ **{file.filename}** loaded & secured.\nReady for analysis.", 
                "timestamp": ts, "metadata": {"agent": "Vault", "privacyScore": 100}
            })

        return {"analysis": "File Processed", "session_id": sid, "privacyScore": 100}

    except Exception as e:
        return {"error": str(e)}

@app.post("/analyze")
async def analyze(data: AnalyzeRequest):
    sid = data.session_id or str(uuid.uuid4())
    
    # Recovery
    if sid not in active_sessions:
        print(f"🔄 Recovering session {sid} from Cloud DB...")
        r_data, r_type = file_store.load_file(sid)
        if r_data is not None:
            active_sessions[sid] = {"data": r_data, "type": r_type}
    
    session_data = active_sessions.get(sid)
    
    try:
        # 1. DETECT & TRANSLATE
        translation_result = translator.detect_and_translate(data.text)
        english_query = translation_result.get("english_query", data.text)
        user_lang = translation_result.get("detected_language", "English")
        
        print(f"🌍 Detected: {user_lang} | Query: {english_query}")

        # 2. ANALYZE
        raw_response = ""
        agent_used = "Chat"

        if session_data:
            agent_used = "Analyst"
            raw_response = analyst.analyze_data(
                session_data["data"], 
                session_data["type"], 
                english_query, 
                sid
            )
        else:
            agent_used = "Liaison"
            raw_response = generate_content_robust(f"User Query: {english_query}")

        # 3. TRANSLATE BACK
        final_response = translator.translate_response(
            raw_response, 
            user_lang, 
            mode=data.translation_mode 
        )

    except Exception as e:
        final_response = f"⚠️ System Error: {str(e)}"
        agent_used = "System"

    # Save
    if db is not None:
        ts = datetime.now().isoformat()
        db.messages.insert_one({"session_id": sid, "role": "user", "content": data.text, "timestamp": ts})
        db.messages.insert_one({
            "session_id": sid, "role": "assistant", "content": final_response, 
            "metadata": {"agent": agent_used, "language": user_lang, "mode": data.translation_mode}, "timestamp": ts
        })
        db.sessions.update_one({"session_id": sid}, {"$set": {"updated_at": ts}})

    return {"analysis": final_response, "session_id": sid, "agent": agent_used}

# ... (Keep get_sessions, get_messages, delete_session)
@app.get("/sessions")
async def get_sessions(user_email: str = Header(None)):
    if db is None or not user_email: return []
    try:
        cursor = db.sessions.find({"user_email": user_email}).sort("created_at", -1)
        return [{**{k:v for k,v in d.items() if k!="_id"}, "id": d["session_id"]} for d in cursor]
    except: return []

@app.get("/sessions/{sid}/messages")
async def get_messages(sid: str):
    if db is None: return []
    cursor = db.messages.find({"session_id": sid}).sort("timestamp", 1)
    return [{**{k:v for k,v in d.items() if k!="_id"}, "id": str(d["_id"])} for d in cursor]

@app.delete("/sessions/{sid}")
async def delete_session(sid: str):
    if db is None: return {"error": "DB not connected"}
    db.sessions.delete_one({"session_id": sid})
    db.messages.delete_many({"session_id": sid})
    db.vault_mappings.delete_one({"session_id": sid})
    db.file_storage.delete_one({"session_id": sid})
    active_sessions.pop(sid, None)
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)