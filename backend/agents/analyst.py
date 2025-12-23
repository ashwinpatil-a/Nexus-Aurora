import pandas as pd
import json
import io

class AnalystAgent:
    def __init__(self, vault_agent):
        self.vault = vault_agent

    def analyze_bytes(self, filename: str, file_bytes: bytes, ai_runner):
        content_str = ""
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_bytes))
                content_str = df.head(50).to_string()
            elif filename.endswith('.json'):
                data = json.loads(file_bytes.decode('utf-8'))
                content_str = json.dumps(data, indent=2)
            else:
                content_str = file_bytes.decode('utf-8', errors='ignore')[:5000]
        except Exception as e:
            return f"Error reading file: {str(e)}", 0, ""

        # Zero-Trust Encryption
        safe_content, score = self.vault.protect(content_str)
        
        # AI Analysis
        prompt = f"Analyze this data safely. Treat tokens like <PERSON_1> as real variables.\n\nDATA:\n{safe_content}"
        try:
            raw_analysis = ai_runner(prompt)
        except:
            raw_analysis = "Analysis failed."

        # Restore Real Data for User
        final_analysis = self.vault.restore(raw_analysis)
        return final_analysis, score, safe_content