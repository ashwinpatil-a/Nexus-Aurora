import google.generativeai as genai

class SentinelAgent:
    def audit_code(self, code_snippet: str):
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""
        ROLE: Elite Cyber Security Auditor.
        TASK: Analyze this code for vulnerabilities (SQLi, XSS, Buffer Overflow).
        OUTPUT: JSON format with 'risk_level' and 'remediation'.
        
        CODE:
        {code_snippet}
        """
        return model.generate_content(prompt).text