# backend/agents/analyst.py
import pandas as pd
import sys
import io
import re
import ast
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

            # 🟢 PROMPT FIX: SEPARATE TEXT AND DATA
            prompt = f"""
            Role: Python Data Analyst.
            Task: Answer query "{safe_query}" using `df`.
            
            SCHEMA:
            {schema_info}
            
            SAMPLE:
            {head_view}
            
            RULES:
            1. **SEARCH:** For text searches (e.g. "France"), use `df[df['col'].str.contains('France', case=False)]`.
            2. **CHART:** If specific data is asked for plotting:
               - Create `chart_data = {{ "type": "bar", "data": [{{"label": "A", "value": 10}}, ...] }}`
               - IMPORTANT: Do NOT put this JSON in the `result` variable.
            3. **TEXT OUTPUT:** In `result`, write a human-readable summary (e.g., "Here is the sales data by country. The top country is X.").
               - Do NOT print the raw JSON dictionary in `result`.
            
            RETURN ONLY PYTHON CODE.
            """
            
            try:
                response_text = self.call_model(prompt)
                clean_code = self._extract_code(response_text)

                if not clean_code: return f"Error: No code generated.", None
                
                local_env = {'df': df, 'pd': pd, 'result': None, 'chart_data': None}
                old_stdout = sys.stdout
                redirected_output = io.StringIO()
                sys.stdout = redirected_output
                
                try:
                    exec(clean_code, {}, local_env)
                except Exception as e:
                    sys.stdout = old_stdout
                    if "tabulate" in str(e):
                        try: exec(clean_code.replace(".to_markdown()", ".to_string()"), {}, local_env)
                        except: return f"Error: {e}", None
                    else:
                        return f"Error: {str(e)}", None

                sys.stdout = old_stdout
                result = local_env.get('result')
                chart_data = local_env.get('chart_data')
                
                if result is None: 
                    result = redirected_output.getvalue()

                # If the AI accidentally made 'result' a dict/json string equal to chart_data, fix it
                if isinstance(result, (dict, list)) or (isinstance(result, str) and result.strip().startswith("{'type':")):
                    result = "Here is the visualized data based on your request."

                final_text = self.vault.restore(str(result), session_id=session_id)
                
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
            prompt = f"Find: {safe_query}\n\nDoc:\n{data_packet[:20000]}"
            response_text = self.call_model(prompt)
            return self.vault.restore(response_text, session_id=session_id), None

        return "Unsupported format.", None