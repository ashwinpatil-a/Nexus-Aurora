import pandas as pd
import sys
import io
import re
import json

class AnalystAgent:
    def __init__(self, model_caller, vault_agent):
        self.call_model = model_caller
        self.vault = vault_agent

    def _extract_code(self, text: str):
        match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
        if match: return match.group(1).strip()
        match = re.search(r"```\s*(.*?)```", text, re.DOTALL)
        if match: return match.group(1).strip()
        if "df" in text and ("=" in text or "print" in text): return text.strip()
        return None

    def analyze_data(self, data_packet, data_type: str, english_query: str, session_id: str):
        safe_query, _ = self.vault.protect(english_query, session_id=session_id)

        if data_type == "structured":
            df = data_packet
            buffer = io.StringIO()
            df.info(buf=buffer)
            schema_info = buffer.getvalue()
            head_view = df.head(3).to_string()

            # 🟢 UPDATED PROMPT: BANS MATPLOTLIB, FORCES JSON CHART
            prompt = f"""
            Role: Python Data Analyst.
            Task: Answer query "{safe_query}" using `df`.
            
            SCHEMA:
            {schema_info}
            
            SAMPLE:
            {head_view}
            
            RULES:
            1. **NO MATPLOTLIB / NO PLOTTING LIBRARIES**: The server cannot display images. Do not import matplotlib or seaborn.
            2. **CHARTS**: If visual data is asked:
               - You MUST construct a dictionary named `chart_data`.
               - Format: `chart_data = {{ "title": "Chart Title", "type": "bar", "data": [{{"label": "Item A", "value": 10}}, {{"label": "Item B", "value": 20}}] }}`
               - Keep the number of bars under 10 (aggregate if needed).
            3. **TEXT OUTPUT**: Write a human-readable answer in the `result` variable.
               - Example: `result = "I found 5 rows matching France..."`
               - If you do not assign `result`, the user will see nothing.
            
            RETURN ONLY PYTHON CODE.
            """
            
            try:
                response_text = self.call_model(prompt)
                clean_code = self._extract_code(response_text)

                if not clean_code: return f"Error: No code generated.", None
                
                # 🟢 Pre-define chart_data as None so the AI can populate it
                local_env = {'df': df, 'pd': pd, 'result': None, 'chart_data': None}
                
                # Capture standard output just in case
                old_stdout = sys.stdout
                redirected_output = io.StringIO()
                sys.stdout = redirected_output
                
                try:
                    exec(clean_code, {}, local_env)
                except Exception as e:
                    sys.stdout = old_stdout
                    # Fallback: simple print if code fails
                    if "matplotlib" in str(e):
                        return "⚠️ Error: The AI tried to use Matplotlib. Please ask it to 'summarize data' instead of plotting.", None
                    return f"Error executing code: {str(e)}", None

                sys.stdout = old_stdout
                
                # Retrieve variables
                result = local_env.get('result')
                chart_data = local_env.get('chart_data')
                
                # Fallback if 'result' variable was ignored by AI
                if result is None: 
                    result = redirected_output.getvalue()

                # Safety: Ensure result is a string
                if not result or not str(result).strip():
                     result = "✅ Analysis complete. (See chart below)" if chart_data else "✅ Done."

                # Restore privacy tokens
                final_text = self.vault.restore(str(result), session_id=session_id)
                
                # Restore privacy tokens inside the chart data too
                if chart_data:
                    try:
                        c_str = json.dumps(chart_data)
                        c_res = self.vault.restore(c_str, session_id=session_id)
                        chart_data = json.loads(c_res)
                    except: pass

                return final_text, chart_data

            except Exception as e:
                return f"System Error: {str(e)}", None

        elif data_type == "unstructured":
            # (Unchanged logic for text files)
            prompt = f"Find: {safe_query}\n\nDoc:\n{data_packet[:20000]}"
            response_text = self.call_model(prompt)
            return self.vault.restore(response_text, session_id=session_id), None

        return "Unsupported format.", None