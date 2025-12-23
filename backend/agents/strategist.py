import google.generativeai as genai

class StrategistAgent:
    def generate_report(self, text: str):
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"Convert this raw data into a C-Suite Executive Summary. Focus on ROI and Actionable Insights:\n{text}"
        return model.generate_content(prompt).text