import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# 1. Load Env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ Error: GOOGLE_API_KEY not found in .env")
    exit()

# 2. Initialize Client
client = genai.Client(api_key=api_key)

# 3. List Models
print("🔍 Checking available models for your API key...\n")
try:
    # We iterate and print the name directly
    for m in client.models.list():
        print(f"✅ Found: {m.name}")
except Exception as e:
    print(f"❌ Error listing models: {e}")