import os
import uvicorn
import google.generativeai as genai
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from supabase import create_client, Client
import uuid # For validating IDs

# --- IMPORT PRIVACY VAULT ---
from privacy_vault import vault 

app = FastAPI()

# --- CONFIGURATION ---


# Initialize Clients
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

openai_client = None
if os.environ.get("OPENAI_API_KEY"):
    openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RequestData(BaseModel):
    text: str
    session_id: str = None
    preferred_model: str = "auto"

# --- DEBUG: PRINT AVAILABLE MODELS ---
print("\n🔍 Checking available Google Models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"   - {m.name}")
except Exception as e:
    print(f"⚠️ Could not list models: {e}")

# --- SMART ROUTER ---
def get_gemini_response(prompt):
    # We list the most likely valid names first
    models = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
    
    for model_name in models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text, model_name
        except:
            continue # Try next model
            
    return "Error: No working Gemini model found.", "Offline"

def ask_the_swarm(prompt: str, model_preference: str = "auto"):
    # 1. Try OpenAI (Logic)
    if openai_client and (model_preference == "openai" or "code" in prompt.lower()):
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content, "OpenAI GPT-4o"
        except:
            pass # Fallback

    # 2. Try Gemini (Data)
    return get_gemini_response(prompt)

@app.post("/analyze")
async def analyze(data: RequestData):
    print(f"\n📥 Input: {data.text[:30]}...")
    
    # 1. LOCAL PRIVACY
    safe_text = vault.scrub(data.text)
    print(f"🔒 Scrubbed: {safe_text[:50]}...")

    # 2. CLOUD INTELLIGENCE
    final_prompt = f"Analyze this redacted text. Identify domain and insights: {safe_text}"
    insight, engine_used = ask_the_swarm(final_prompt, data.preferred_model)

    # 3. SAVE TO MEMORY (With UUID Validation)
    if data.session_id:
        try:
            # Validate if it's a real UUID to prevent Database Error 22P02
            uuid_obj = uuid.UUID(data.session_id)
            
            supabase.table("chat_messages").insert({
                "session_id": str(uuid_obj),
                "role": "user",
                "content": data.text,
                "metadata": {"scrubbed": False}
            }).execute()
            
            supabase.table("chat_messages").insert({
                "session_id": str(uuid_obj),
                "role": "assistant",
                "content": insight,
                "metadata": {"engine": engine_used}
            }).execute()
            print("💾 Saved to Memory")
        except ValueError:
            print(f"⚠️ Skipping DB Save: '{data.session_id}' is not a valid UUID.")
        except Exception as e:
            print(f"⚠️ Database Error: {e}")

    return {
        "original_redacted": safe_text,
        "analysis": insight,
        "engine": engine_used
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)