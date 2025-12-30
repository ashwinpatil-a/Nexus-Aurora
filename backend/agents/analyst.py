import pandas as pd
import sys
import io
import re
import ast
import traceback

class AnalystAgent:
    def __init__(self, vault_agent):
        self.vault = vault_agent

    def _extract_code(self, text: str) -> str:
        """Extracts ONLY valid Python code blocks."""
        match = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
        if match: return match.group(1).strip()
        
        match = re.search(r"```\s*(.*?)```", text, re.DOTALL)
        if match: return match.group(1).strip()
        
        return None

    def analyze_data(self, data_packet, data_type: str, user_query: str, ai_runner, session_id: str):
        # 1. Secure Query
        safe_query, _ = self.vault.protect(user_query, session_id=session_id)

        # === MODE A: STRUCTURED (CSV, Excel) ===
        if data_type == "structured":
            df = data_packet
            
            # Send Schema & Sample so AI knows column names
            buffer = io.StringIO()
            df.info(buf=buffer)
            schema_info = buffer.getvalue()
            head_view = df.head(3).to_string()

            # 🟢 PROMPT: EXECUTION FOCUSED
            prompt = f"""
            You are a Python Data Analyst.
            I have a DataFrame `df` loaded in memory.
            
            METADATA (Column Names & Types):
            {schema_info}
            
            SAMPLE DATA (First 3 rows):
            {head_view}
            
            USER REQUEST: "{safe_query}"
            
            TASK: 
            1. Identify the relevant columns based on the user request (e.g., if asking for "descriptions", find the column named 'Description', 'Desc', or similar).
            2. Write Python Pandas code to calculate the answer.
            3. Store the final result in a variable named `result`.
            4. If the result is a DataFrame (multiple rows), format `result` as a MARKDOWN TABLE string using `.to_markdown()`.
            
            STRICT CONSTRAINTS:
            - DO NOT explain. DO NOT ask for column names. Figure it out from the Metadata.
            - DO NOT use print().
            - RETURN ONLY THE PYTHON CODE inside ```python``` blocks.
            """
            
            try:
                # 1. Get Code
                raw_response = ai_runner(prompt)
                clean_code = self._extract_code(raw_response)
                
                # Safety Check
                if not clean_code:
                    return f"**Analysis Note:** I couldn't generate code. Raw response: {raw_response}", 0

                try:
                    ast.parse(clean_code) # Syntax Check
                except SyntaxError:
                    return f"**Error:** Generated invalid code.", 0

                # 2. Execute Code
                local_env = {'df': df, 'pd': pd, 'result': None}
                old_stdout = sys.stdout
                redirected_output = io.StringIO()
                sys.stdout = redirected_output
                
                try:
                    exec(clean_code, {}, local_env)
                except Exception as exec_error:
                    sys.stdout = old_stdout
                    return f"**Calculation Error:**\n`{str(exec_error)}`", 0

                sys.stdout = old_stdout
                execution_result = local_env.get('result')
                print_output = redirected_output.getvalue()

                # 3. Format Output
                if execution_result is None and print_output:
                    execution_result = print_output
                
                # If result is already a markdown string (from .to_markdown()), use it
                raw_output = str(execution_result)
                
                # 4. Final Polish: Show the Result directly
                human_response = ai_runner(
                    f"The code calculated this result:\n\n{raw_output}\n\nTask: Present this answer to the user. If it looks like a table, keep the table format. Do not explain the code."
                )
                
                return self.vault.restore(human_response, session_id=session_id), 100

            except Exception as e:
                return f"System Error: {str(e)}", 0

        # === MODE B: UNSTRUCTURED (Text/PDF) ===
        elif data_type == "unstructured":
            prompt = f"""
            Analyze this text content and answer the user's question directly.
            Format the answer as a Markdown Table or Bullet Points if applicable.
            
            TEXT CONTENT (First 20k chars):
            {data_packet[:20000]}
            
            USER QUERY: {safe_query}
            """
            response = ai_runner(prompt)
            return self.vault.restore(response, session_id=session_id), 100

        return "Unsupported data format.", 0