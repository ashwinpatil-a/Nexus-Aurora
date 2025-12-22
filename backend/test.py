import google.generativeai as genai
import os

# PASTE YOUR KEY HERE
os.environ["GOOGLE_API_KEY"] = "AIzaSyD5PaS2hSK1AALvp8A-91pWv_V9vkdhB7c"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

print("🔍 Connecting to Google...")
try:
    print("✅ AVAILABLE MODELS:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"   👉 {m.name}")
except Exception as e:
    print(f"❌ ERROR: {e}")