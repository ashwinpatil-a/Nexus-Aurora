# backend/main.py
import os
import uvicorn
import uuid
import certifi
import sys
import time
import io
import re
import ast
import pickle
import bson.binary
import pandas as pd
import random
import traceback
from datetime import datetime
from typing import Optional, Dict
from pathlib import Path

from fastapi import FastAPI, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv
from google import genai
from pypdf import PdfReader 

# =========================================================
# 1. SETUP & CONFIGURATION
# =========================================================
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

MONGO_URI = os.getenv("MONGO_URI")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not MONGO_URI or not GOOGLE_API_KEY:
    raise RuntimeError("❌ CRITICAL: Missing MONGO_URI or GOOGLE_API_KEY in .env")

# --- Clients ---
genai_client = genai.Client(api_key=GOOGLE_API_KEY)

try:
    mongo_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = mongo_client["nexus_db"]
    mongo_client.admin.command("ping")
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

# Global Cache (for speed only; source of truth is MongoDB)
active_sessions: Dict[str, dict] = {} 

class AnalyzeRequest(BaseModel):
    text: str
    session_id: Optional[str] = None
    user_email: str = "anonymous"

# =========================================================
# 2. CORE UTILITIES
# =========================================================

class MongoFileStore:
    def __init__(self, database):
        self.db = database

    def save_file(self, session_id, data, data_type, filename):
        if self.db is None: return False
        try:
            if data_type == "structured":
                content_binary = pickle.dumps(data)
            else:
                content_binary = data.encode('utf-8')

            self.db.file_storage.update_one(
                {"session_id": session_id},
                {"$set": {
                    "session_id": session_id,
                    "filename": filename,
                    "data_type": data_type,
                    "content": bson.binary.Binary(content_binary),
                    "updated_at": datetime.now()
                }},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"❌ Storage Error: {e}")
            return False

    def load_file(self, session_id):
        if self.db is None: return None, None
        doc = self.db.file_storage.find_one({"session_id": session_id})
        if not doc: return None, None
        try:
            if doc["data_type"] == "structured":
                data = pickle.loads(doc["content"])
            else:
                data = doc["content"].decode('utf-8')
            return data, doc["data_type"]
        except Exception as e:
            print(f"❌ Retrieval Error: {e}")
            return None, None

def load_file_universally(filename: str, file_bytes: bytes):
    filename = filename.lower()
    try:
        if filename.endswith('.csv'):
            return pd.read_csv(io.BytesIO(file_bytes)), "structured"
        elif filename.endswith('.json'):
            return pd.read_json(io.BytesIO(file_bytes)), "structured"
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            return pd.read_excel(io.BytesIO(file_bytes)), "structured"
        elif filename.endswith('.parquet'):
            return pd.read_parquet(io.BytesIO(file_bytes)), "structured"
        elif filename.endswith('.pdf'):
            reader = PdfReader(io.BytesIO(file_bytes))
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            return text, "unstructured"
        elif filename.endswith('.txt') or filename.endswith('.md'):
            return file_bytes.decode('utf-8', errors='ignore'), "unstructured"
        return None, "unsupported"
    except Exception as e:
        print(f"❌ Loader Error: {e}")
        return None, "error"

# =========================================================
# 3. INTELLIGENT AGENT ENGINE (UPDATED MODELS)
# =========================================================

def get_smart_response(prompt: str):
    """
    Agentic Retry Logic using YOUR available models.
    """
    # 🟢 CHANGED: Using models confirmed in your 'test.py' logs
    models = [
        "gemini-2.5-flash",      # Fastest, newest
        "gemini-2.0-flash",      # Stable fallback
        "gemini-2.5-pro",        # High intelligence
    ]
    
    last_exception = None

    for model in models:
        for attempt in range(2):
            try:
                response = genai_client.models.generate_content(
                    model=model, 
                    contents=prompt
                )
                if response.text:
                    return response.text
            except Exception as e:
                last_exception = e
                error_str = str(e)
                
                # Rate Limit Backoff
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    wait_time = 2
                    print(f"⚠️ Quota hit on {model}. Sleeping {wait_time}s...")
                    time.sleep(wait_time)
                    continue 
                elif "404" in error_str or "NOT_FOUND" in error_str:
                    print(f"⚠️ {model} not found. Switching...")
                    break
                else:
                    print(f"⚠️ {model} error: {e}")
                    break 
                    
    raise RuntimeError(f"Google API Error: {str(last_exception)}")

class AgenticAnalyst:
    """The Brain: Validates logic before execution."""
    def __init__(self, db):
        self.db = db

    def _extract_code(self, text: str):
        match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
        if match: return match.group(1).strip()
        match = re.search(r"```\s*(.*?)```", text, re.DOTALL)
        if match: return match.group(1).strip()
        return None

    def execute_analysis(self, df: pd.DataFrame, query: str):
        # Prepare Schema
        buffer = io.StringIO()
        df.info(buf=buffer)
        schema_info = buffer.getvalue()
        head_view = df.head(3).to_string()

        prompt = f"""
        Role: Senior Data Analyst.
        Task: Write Python Pandas code to answer the user query.
        
        DATASET SCHEMA:
        {schema_info}
        
        SAMPLE ROWS:
        {head_view}
        
        USER QUERY: "{query}"
        
        STRICT RULES:
        1. Assume `df` is already loaded.
        2. Store the result in a variable named `result`.
        3. If the result is a table, TRY to format it as Markdown: `result = df_subset.to_markdown()`.
        4. DO NOT use print().
        5. RETURN ONLY PYTHON CODE inside ```python``` blocks.
        """

        try:
            # 1. Get Code
            raw_response = get_smart_response(prompt)
            clean_code = self._extract_code(raw_response)

            if not clean_code:
                return f"**Analysis Note:**\n{raw_response}"
            
            try:
                ast.parse(clean_code)
            except SyntaxError:
                return f"**Error:** The AI generated invalid code. Please ask again."

            # 2. Execute with SELF-HEALING
            local_env = {'df': df, 'pd': pd, 'result': None}
            old_stdout = sys.stdout
            redirected_output = io.StringIO()
            sys.stdout = redirected_output

            try:
                exec(clean_code, {}, local_env)
            except Exception as e:
                # 🟢 SELF-HEALING LOGIC
                if "tabulate" in str(e):
                    # If tabulate is missing, fallback to standard string format
                    print("⚠️ 'tabulate' missing. Falling back to standard table.")
                    fallback_code = clean_code.replace(".to_markdown()", ".to_string()")
                    try:
                        exec(fallback_code, {}, local_env)
                    except Exception as fallback_error:
                        sys.stdout = old_stdout
                        return f"**Calculation Error:**\n`{str(fallback_error)}`"
                else:
                    sys.stdout = old_stdout
                    return f"**Calculation Error:**\n`{str(e)}`"

            sys.stdout = old_stdout
            result = local_env.get('result')
            print_output = redirected_output.getvalue()

            if result is None and print_output:
                result = print_output

            # 3. Polish
            final_answer = str(result)
            polish_prompt = f"User asked: {query}\nCode Result:\n{final_answer}\n\nTask: Present this answer clearly. Keep Markdown tables intact."
            polished_response = get_smart_response(polish_prompt)
            return polished_response

        except RuntimeError as e:
            return f"⚠️ **AI Error:** {str(e)}"
        except Exception as e:
            return f"**System Error:** {str(e)}"
# =========================================================
# 4. API ENDPOINTS
# =========================================================

file_store = MongoFileStore(db)
analyst = AgenticAnalyst(db)

@app.post("/upload")
async def upload(file: UploadFile = File(...), user_email: str = Header("anonymous")):
    sid = str(uuid.uuid4())
    try:
        content = await file.read()
        
        # 1. Load
        data, dtype = load_file_universally(file.filename, content)
        if data is None: return {"error": "Unsupported file format"}

        # 2. Persist
        file_store.save_file(sid, data, dtype, file.filename)
        active_sessions[sid] = {"data": data, "type": dtype}

        # 3. Log
        ts = datetime.now().isoformat()
        if db is not None:
            db.sessions.insert_one({
                "session_id": sid, "user_email": user_email, "title": file.filename, "created_at": ts, "file_attached": True
            })
            db.messages.insert_one({
                "session_id": sid, "role": "assistant", "content": f"✅ **{file.filename}** loaded.", "timestamp": ts
            })

        return {"analysis": "File Processed", "session_id": sid, "privacyScore": 100}

    except Exception as e:
        print(f"❌ Upload Error: {e}")
        return {"error": str(e)}

@app.post("/analyze")
async def analyze(data: AnalyzeRequest):
    sid = data.session_id or str(uuid.uuid4())
    
    # 1. Recovery Logic
    if sid not in active_sessions:
        print(f"🔄 Fetching session {sid} from Cloud DB...")
        r_data, r_type = file_store.load_file(sid)
        if r_data is not None:
            active_sessions[sid] = {"data": r_data, "type": r_type}
    
    session_data = active_sessions.get(sid)
    response_text = ""

    # 2. Execution
    if session_data and session_data["type"] == "structured":
        response_text = analyst.execute_analysis(session_data["data"], data.text)
    elif session_data and session_data["type"] == "unstructured":
        try:
            prompt = f"Analyze this text: {data.text}\n\nContext:\n{session_data['data'][:15000]}"
            response_text = get_smart_response(prompt)
        except RuntimeError as e:
            response_text = f"⚠️ AI Error: {str(e)}"
    else:
        try:
            response_text = get_smart_response(f"User: {data.text}")
        except RuntimeError as e:
            response_text = f"⚠️ AI Error: {str(e)}"

    # 3. Save History
    if db is not None:
        ts = datetime.now().isoformat()
        db.messages.insert_one({"session_id": sid, "role": "user", "content": data.text, "timestamp": ts})
        db.messages.insert_one({"session_id": sid, "role": "assistant", "content": response_text, "timestamp": ts})
        db.sessions.update_one({"session_id": sid}, {"$set": {"updated_at": ts}})

    return {"analysis": response_text, "session_id": sid}

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
    db.file_storage.delete_one({"session_id": sid})
    active_sessions.pop(sid, None)
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)