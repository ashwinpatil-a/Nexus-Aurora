import json
import re

class TranslatorAgent:
    def __init__(self, model_caller):
        self.call_model = model_caller

    def detect_and_translate(self, user_text: str):
        prompt = f"""
        Role: Translator.
        Input: "{user_text}"
        Task: Identify language and translate to English.
        
        CRITICAL: Output strictly valid JSON. No markdown formatting.
        Format: {{"detected_language": "Lang", "english_query": "Text"}}
        """
        try:
            # We pass json_mode=True, but main.py will ignore it if the model is Gemma
            response_text = self.call_model(prompt, json_mode=True)
            
            if "Error" in response_text: 
                return {"detected_language": "English", "english_query": user_text}
            
            # Cleanup for models that might still add markdown
            cleaned = response_text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except:
            return {"detected_language": "English", "english_query": user_text}

    def translate_response(self, english_response: str, target_language: str, mode: str = "mixed"):
        if target_language.lower() in ["english", "en", "unknown"]:
            return english_response

        instructions = "Translate EXPLANATIONS to target language. KEEP DATA IN ENGLISH." if mode == "mixed" else "FULLY TRANSLATE everything."
        
        prompt = f"""
        Task: {instructions} -> {target_language}
        Text:
        {english_response}
        """
        try:
            return self.call_model(prompt)
        except:
            return english_response