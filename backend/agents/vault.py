from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
import uuid

class VaultAgent:
    def __init__(self):
        # Use 'sm' model for speed/reliability as per your setup
        conf = {"nlp_engine_name": "spacy", "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}]}
        provider = NlpEngineProvider(nlp_configuration=conf)
        self.analyzer = AnalyzerEngine(nlp_engine=provider.create_engine())
        self.token_map = {} 

    def protect(self, text: str):
        if not text: return "", 100
        results = self.analyzer.analyze(text=text, entities=["PHONE_NUMBER", "EMAIL_ADDRESS", "PERSON", "LOCATION"], language='en')
        
        safe_text = text
        for res in sorted(results, key=lambda x: x.start, reverse=True):
            original = text[res.start:res.end]
            token = f"<{res.entity_type}_{uuid.uuid4().hex[:4].upper()}>"
            self.token_map[token] = original
            safe_text = safe_text[:res.start] + token + safe_text[res.end:]
            
        score = max(0, 100 - (len(results) * 10))
        return safe_text, score

    def restore(self, text: str):
        restored = text
        for token, original in self.token_map.items():
            if token in restored:
                restored = restored.replace(token, original)
        return restored