import os
import uvicorn
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import FastAPI, Header, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import certifi
import uuid
from datetime import datetime
import google.generativeai as genai

from agents.vault import VaultAgent
from agents.router import SwarmRouter
from agents.analyst import AnalystAgent

# 1. SETUP FIREBASE & MONGO
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

# Replace with YOUR MongoDB Atlas Connection String
MONGO_URI = "mongodb+srv://admin:avp1810@cluster0.vj68psd.mongodb.net/?appName=Cluster0"

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client["nexus_db"]
    print("✅ Connected to MongoDB Atlas")
except Exception as e:
    print(f"❌ MongoDB Error: {e}")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

os.environ["GOOGLE_API_KEY"] = # <--- PASTE GEMINI KEY
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# 2. INITIALIZE SWARM
vault = VaultAgent()
router = SwarmRouter()
analyst = AnalystAgent(vault)

def ask_gemini_swarm(prompt):
    models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']
    for m in models:
        try: return genai.GenerativeModel(m).generate_content(prompt).text
        except: continue
    return "Error: Swarm Offline."

# 3. ENDPOINTS
@app.get("/sessions")
async def get_sessions(user_email: str = Header(None)):
    if not user_email: return []
    cursor = db.sessions.find({"user_email": user_email}).sort("created_at", -1)
    return [{"id": doc.pop("session_id"), **doc, "_id": str(doc.pop("_id"))} for doc in cursor]

@app.get("/sessions/{sid}/messages")
async def get_messages(sid: str):
    cursor = db.messages.find({"session_id": sid}).sort("timestamp", 1)
    return [{"id": str(doc.pop("_id")), **doc} for doc in cursor]

@app.post("/analyze")
async def analyze(data: dict):
    text = data.get("text", "")
    session_id = data.get("session_id") or str(uuid.uuid4())
    user_email = data.get("user_email", "anonymous")

    # 1. Protect & Route
    safe_text, score = vault.protect(text)
    agent, domain = router.route(safe_text, False)
    
    # 2. Analyze & Restore
    raw_res = ask_gemini_swarm(f"Act as {agent}. {safe_text}")
    final_res = vault.restore(raw_res)

    # 3. Save to Mongo
    db.sessions.update_one({"session_id": session_id}, {"$set": {
        "session_id": session_id, "user_email": user_email, "title": text[:30], 
        "created_at": datetime.now().isoformat(), "domain": domain
    }}, upsert=True)
    
    db.messages.insert_many([
        {"session_id": session_id, "role": "user", "content": text, "timestamp": datetime.now().isoformat()},
        {"session_id": session_id, "role": "assistant", "content": final_res, 
         "metadata": {"agentUsed": agent, "privacyScore": score}, "timestamp": datetime.now().isoformat()}
    ])

    return {"analysis": final_res, "agent": agent, "domain": domain, "privacyScore": score, "session_id": session_id}

@app.post("/upload")
async def upload(file: UploadFile = File(...), user_email: str = Header("anonymous")):
    content = await file.read()
    res, score, preview = analyst.analyze_bytes(file.filename, content, ask_gemini_swarm)
    
    sid = str(uuid.uuid4())
    db.sessions.insert_one({
        "session_id": sid, "user_email": user_email, "title": f"File: {file.filename}",
        "created_at": datetime.now().isoformat(), "domain": "Data Analysis", "file_attached": True
    })
    
    db.messages.insert_many([
        {"session_id": sid, "role": "system", "content": f"🔒 **Vault Encrypted**\nPreview: `{preview[:150]}...`", "timestamp": datetime.now().isoformat()},
        {"session_id": sid, "role": "assistant", "content": res, 
         "metadata": {"agentUsed": "Analyst", "privacyScore": score}, "timestamp": datetime.now().isoformat()}
    ])
    
    return {"analysis": res, "encrypted_preview": preview[:200], "privacyScore": score, "session_id": sid, "agent": "Analyst"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
