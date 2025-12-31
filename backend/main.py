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
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, InternalServerError

# Imports
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
# 🟢 MEGA MODEL ROTATOR (Using ALL your available models)
# =========================================================
def generate_content_robust(prompt: str, json_mode: bool = False):
    """
    Cycles through 20+ models to guarantee uptime.
    """
    # Priority Queue based on Speed > Intelligence > Experimental
    models_to_try = [
        'gemini-2.0-flash',             
        'gemini-2.5-flash',             
        'gemini-1.5-flash',
        'gemini-flash-latest',
        'gemini-2.0-flash-lite-preview-02-05', # Very fast backup
        
        # Smart Models (Slower, stricter quota)
        'gemini-1.5-pro',
        'gemini-pro-latest',
        
        # Experimental / New
        'gemini-2.0-flash-exp',
        'gemini-exp-1206',
        'gemini-2.0-flash-001',
        
        # Open Models (Note: These DO NOT support JSON mode config)
        'gemma-3-27b-it',
        'gemma-3-4b-it' 
    ]
    
    last_err = None
    
    for m in models_to_try:
        try:
            # 🔴 CRITICAL FIX: Gemma models do not support response_mime_type
            # We must disable JSON mode enforcement for them, even if requested.
            current_config = None
            if json_mode and "gemma" not in m:
                current_config = {'response_mime_type': 'application/json'}

            # print(f"Trying model: {m}")
            response = genai_client.models.generate_content(
                model=m, 
                contents=prompt, 
                config=current_config
            )
            return response.text
            
        except Exception as e:
            err_str = str(e)
            
            # Filter for API errors (Quota, Not Found, Overloaded)
            # 400 is included now to catch the Gemma error if it slips through
            if any(x in err_str for x in ["429", "404", "RESOURCE", "NOT_FOUND", "Quota", "busy", "exhausted", "400", "INVALID_ARGUMENT"]):
                last_err = e
                # 🔴 FIX: If quota is hit, wait a split second before hitting the next model
                if "429" in err_str or "Quota" in err_str:
                    time.sleep(1) 
                continue # Skip to next model
            
            print(f"⚠️ Error on {m}: {err_str}")
            continue
            
    print(f"❌ ALL MODELS FAILED. Final error: {last_err}")
    return "Error: System Overloaded. All AI models are currently busy. Please try again."

# 2. INITIALIZE AGENTS
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

# 3. ENDPOINTS
@app.post("/upload")
async def upload(file: UploadFile = File(...), user_email: str = Header("anonymous")):
    sid = str(uuid.uuid4())
    try:
        content = await file.read()
        data, dtype = load_file_universally(file.filename, content)
        if data is None: return {"error": "Unsupported file format"}

        if vault and dtype == "structured":
            data = vault.ingest_file(data, session_id=sid)
        
        file_store.save_file(sid, data, dtype, file.filename)
        active_sessions[sid] = {"data": data, "type": dtype}

        if db is not None:
            ts = datetime.now().isoformat()
            db.sessions.insert_one({"session_id": sid, "user_email": user_email, "title": file.filename, "created_at": ts, "file_attached": True})
            db.messages.insert_one({"session_id": sid, "role": "assistant", "content": f"✅ **{file.filename}** loaded.", "timestamp": ts})

        return {"analysis": "File Processed", "session_id": sid}
    except Exception as e:
        return {"error": str(e)}

@app.post("/analyze")
async def analyze(data: AnalyzeRequest):
    sid = data.session_id or str(uuid.uuid4())
    
    # 1. Recovery
    if sid not in active_sessions:
        r_data, r_type = file_store.load_file(sid)
        if r_data is not None:
            active_sessions[sid] = {"data": r_data, "type": r_type}
        else:
            print(f"⚠️ Session {sid} not found in DB.")
    
    session_data = active_sessions.get(sid)
    
    try:
        # A. Translate
        trans_res = translator.detect_and_translate(data.text)
        eng_query = trans_res.get("english_query", data.text)
        user_lang = trans_res.get("detected_language", "English")
        
        print(f"🌍 Lang: {user_lang} | Query: {eng_query}")

        # B. Analyze
        raw_resp = ""
        chart_data = None
        agent_used = "Chat"

        if session_data:
            agent_used = "Analyst"
            raw_resp, chart_data = analyst.analyze_data(
                session_data["data"], 
                session_data["type"], 
                eng_query, 
                sid
            )
        else:
            agent_used = "Liaison"
            raw_resp = generate_content_robust(f"User Query: {eng_query}")

        # C. Translate Output
        # C. Translate Output
        final_resp = translator.translate_response(raw_resp, user_lang, mode=data.translation_mode)

        # 🟢 FINAL SAFETY CHECK
        if not final_resp or not final_resp.strip():
            final_resp = "⚠️ The analysis finished, but returned no readable content. Please try rephrasing your request."

    except Exception as e:
        final_resp = f"⚠️ System Error: {str(e)}"
        agent_used = "System"
        chart_data = None

    # D. Save History
    if db is not None:
        ts = datetime.now().isoformat()
        db.messages.insert_one({"session_id": sid, "role": "user", "content": data.text, "timestamp": ts})
        db.messages.insert_one({
            "session_id": sid, 
            "role": "assistant", 
            "content": final_resp, 
            "metadata": {"agent": agent_used, "language": user_lang, "chart": chart_data}, 
            "timestamp": ts
        })
        db.sessions.update_one({"session_id": sid}, {"$set": {"updated_at": ts}})

    return {"analysis": final_resp, "chart": chart_data, "session_id": sid, "agent": agent_used}

# Standard Getters
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
    try:
        fdoc = db.file_mappings.find_one({"session_id": sid})
        if fdoc: 
            __import__('gridfs').GridFS(db).delete(fdoc['file_id'])
            db.file_mappings.delete_one({"session_id": sid})
    except: pass
    active_sessions.pop(sid, None)
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)