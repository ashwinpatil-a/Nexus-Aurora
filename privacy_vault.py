# backend/privacy_vault.py
import logging
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NexGen_Vault")

class PrivacyVault:
    def __init__(self):
        logger.info("🛡️  Initializing Enterprise Privacy Engine...")
        
        # 1. FORCE USE OF THE LARGE MODEL (en_core_web_lg)
        # This configuration tells Presidio to load the smart Spacy model
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}],
        }
        
        # Create the NLP engine with the config
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()

        # Pass the engine to the Analyzer
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
        self.anonymizer = AnonymizerEngine()
        
        # MEMORY: Maps Real Data <-> Fake Tags
        self.mapping = {} 
        
        # COUNTERS: To generate unique IDs
        self.counters = {
            "PERSON": 1,
            "LOCATION": 1,
            "ORGANIZATION": 1,
            "PHONE_NUMBER": 1,
            "EMAIL_ADDRESS": 1,
            "DATE_TIME": 1,
            "DEFAULT": 1
        }
        logger.info("✅ Privacy Engine Ready (Model: en_core_web_lg).")

    def get_tag(self, text, entity_type):
        """
        Returns an existing tag if known, else generates a new one.
        """
        if text in self.mapping:
            return self.mapping[text]
        
        # Generate new ID
        count = self.counters.get(entity_type, self.counters["DEFAULT"])
        new_tag = f"<{entity_type}_{count}>"
        
        # Increment counter
        if entity_type in self.counters:
            self.counters[entity_type] += 1
        else:
            self.counters["DEFAULT"] += 1
            
        # Save to Memory
        self.mapping[text] = new_tag
        self.mapping[new_tag] = text
        
        return new_tag

    def scrub(self, text: str):
        """
        Scans text and replaces PII with unique, consistent tags.
        """
        # 1. Analyze (Find the secrets)
        results = self.analyzer.analyze(
            text=text,
            language='en'
        )

        # 2. ASSIGN TAGS IN ORDER
        # Sort by start position to assign IDs naturally (Ashwin=1, Rohan=2)
        results.sort(key=lambda x: x.start)
        
        replacements = []
        for result in results:
            secret_word = text[result.start:result.end]
            tag = self.get_tag(secret_word, result.entity_type)
            replacements.append((result.start, result.end, tag))

        # 3. REPLACE TEXT IN REVERSE
        # Sort descending to prevent index shifting during replacement
        replacements.sort(key=lambda x: x[0], reverse=True)

        scrubbed_text = text
        for start, end, tag in replacements:
            scrubbed_text = scrubbed_text[:start] + tag + scrubbed_text[end:]
        
        return scrubbed_text

# Create a single instance
vault = PrivacyVault()

# --- TEST ZONE ---
if __name__ == "__main__":
    test_msg = "Ashwin works at Google. Rohan also works at Google."
    print(f"\nOriginal: {test_msg}")
    print("-" * 30)
    print(f"Scrubbed: {vault.scrub(test_msg)}")