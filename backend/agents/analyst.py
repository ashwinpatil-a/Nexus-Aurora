# backend/agents/analyst.py
import pandas as pd
import sys
import io
import re
import ast

class AnalystAgent:
    def __init__(self, model_caller, vault_agent):
        self.call_model = model_caller # Uses the robust rotator
        self.vault = vault_agent

    def _extract_code(self, text: str) -> str:
        match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
        if match: return match.group(1).strip()
        match = re.search(r"```\s*(.*?)```", text, re.DOTALL)
        if match: return match.group(1).strip()
        return None

    def analyze_data(self, data_packet, data_type: str, english_query: str, session_id: str):
        # 1. Secure Query
        safe_query, _ = self.vault.protect(english_query, session_id=session_id)

        if data_type == "structured":
            df = data_packet
            buffer = io.StringIO()
            df.info(buf=buffer)
            schema_info = buffer.getvalue()
            head_view = df.head(3).to_string()

            prompt = f"""
            Role: Python Data Analyst.
            Task: Write Python Pandas code to answer the query.
            
            SCHEMA:
            {schema_info}
            
            SAMPLE DATA:
            {head_view}
            
            QUERY: "{safe_query}"
            
            CRITICAL RULES:
            1. Assume `df` is loaded.
            2. Store the final output in variable `result`.
            3. NO TRUNCATION: If the user asks to "show", "list", or "display" items, DO NOT return a summary like `['A', 'B', ...]`.
               - Instead, convert it to a full string: `result = '\\n'.join(unique_list)`.
               - Or use: `pd.set_option('display.max_rows', None); result = df_subset.to_markdown()`.
            4. If the result is a huge list (over 100 items), format it as a clean list or table, NOT a Python list string.
            5. RETURN ONLY PYTHON CODE.
            """
            
            try:
                # Call robust model
                response_text = self.call_model(prompt)
                clean_code = self._extract_code(response_text)

                if not clean_code: return f"No code generated. Output: {response_text}"
                
                try: ast.parse(clean_code)
                except SyntaxError: return "Error: Invalid Python code generated."

                # Execute
                local_env = {'df': df, 'pd': pd, 'result': None}
                old_stdout = sys.stdout
                redirected_output = io.StringIO()
                sys.stdout = redirected_output
                
                try:
                    exec(clean_code, {}, local_env)
                except Exception as e:
                    sys.stdout = old_stdout
                    if "tabulate" in str(e):
                        try:
                            exec(clean_code.replace(".to_markdown()", ".to_string()"), {}, local_env)
                        except Exception as fe:
                            return f"Calculation Error: {fe}"
                    else:
                        return f"Calculation Error: {str(e)}"

                sys.stdout = old_stdout
                result = local_env.get('result')
                
                # Restore names (Vault)
                return self.vault.restore(str(result), session_id=session_id)

            except Exception as e:
                return f"System Error: {str(e)}"

        elif data_type == "unstructured":
            prompt = f"Analyze this text: {safe_query}\n\nContext:\n{data_packet[:15000]}"
            response_text = self.call_model(prompt)
            return self.vault.restore(response_text, session_id=session_id)

        return "Unsupported data format."