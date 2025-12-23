import google.generativeai as genai

class LiaisonAgent:
    def chat(self, text: str):
        model = genai.GenerativeModel('gemini-pro')
        return model.generate_content(f"You are Nexus Aurora. Be helpful and concise. User: {text}").text