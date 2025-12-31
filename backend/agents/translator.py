# backend/agents/translator.py
import json
import re

class TranslatorAgent:
    def __init__(self, model_caller):
        # Use the robust function from main.py
        self.call_model = model_caller

    def detect_and_translate(self, user_text: str):
        prompt = f"""
        Role: Expert Technical Translator.
        
        USER INPUT: "{user_text}"
        
        TASK:
        1. Identify the language.
        2. Translate to PRECISE TECHNICAL ENGLISH.
        3. Do NOT generalize nouns (e.g. Keep "Descriptions" as "Descriptions").
        
        JSON OUTPUT:
        {{
            "detected_language": "Language Name",
            "english_query": "Translated Text"
        }}
        """
        try:
            response_text = self.call_model(prompt, json_mode=True)
            cleaned = response_text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except Exception as e:
            print(f"Translation Error: {e}")
            return {"detected_language": "English", "english_query": user_text}

    def translate_response(self, english_response: str, target_language: str, mode: str = "mixed"):
        if target_language.lower() in ["english", "en", "unknown"]:
            return english_response

        # Option 2: Mixed Mode (Default)
        if mode == "mixed":
            instructions = f"""
            Task: Translate the EXPLANATIONS and SENTENCES into {target_language}.
            
            CRITICAL RULES:
            1. KEEP DATA, LISTS, and MARKDOWN TABLES IN ENGLISH (Do not translate the items inside).
            2. Translate only the summaries (e.g., "Here is the list of items:").
            3. If there is a long list of items, leave them EXACTLY as they are.
            """
        
        # Option 1: Mirror Mode
        else:
            instructions = f"Task: FULLY TRANSLATE everything into {target_language}."

        prompt = f"""
        {instructions}
        
        IMPORTANT: Keep Markdown formatting (tables, bold, lists) EXACTLY as is.
        
        TEXT TO PROCESS:
        {english_response}
        """
        
        try:
            return self.call_model(prompt)
        except:
            return english_response