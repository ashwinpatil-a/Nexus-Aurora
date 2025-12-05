import os
from openai import OpenAI
import google.generativeai as genai

# Hardcoded keys from your previous file

# --- 1. Test OpenAI ---
print("--- Starting OpenAI Test ---")
try:
    openai_client = OpenAI(api_key=OPENAI_API_KEY_TEST)
    
    # Try a simple model list call which requires valid auth
    models = openai_client.models.list()
    
    if models.data:
        print("✅ SUCCESS: OpenAI Client initialized and connected.")
    else:
        print("⚠️ WARNING: OpenAI Client initialized but returned no model data.")

except Exception as e:
    print(f"❌ FAILURE: OpenAI connection failed. Error: {e}")

# --- 2. Test Gemini ---
print("\n--- Starting Gemini Test ---")
try:
    genai.configure(api_key=GEMINI_API_KEY_TEST)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Try a simple generation to confirm the model loads and key works
    response = model.generate_content("Say 'Test successful' and nothing else.")
    
    if "Test successful" in response.text:
        print("✅ SUCCESS: Gemini Client initialized and connected.")
    else:
        print(f"⚠️ WARNING: Gemini Client initialized but failed generation. Response: {response.text}")

except Exception as e:
    print(f"❌ FAILURE: Gemini connection failed. Error: {e}")

print("--- Test Complete ---")