import pandas as pd
import re
import logging
import numpy as np

# Setup logging
logging.basicConfig(level=logging.ERROR)

class VaultAgent:
    def __init__(self, mongo_db=None):
        self.db = mongo_db  # Connection to MongoDB

    def _get_map(self, session_id):
        """Fetch the token map for a specific session."""
        if self.db is None or not session_id: 
            return {}, {}
            
        doc = self.db.vault_mappings.find_one({"session_id": session_id})
        if doc:
            return doc.get("forward", {}), doc.get("reverse", {})
        return {}, {}

    def ingest_file(self, df: pd.DataFrame, session_id: str):
        """
        UNIVERSAL INGESTION ENGINE:
        1. Scans ALL columns.
        2. Auto-detects 'Context' columns (Descriptions) and skips them.
        3. Tokenizes 'Entity' columns (IDs, Names, Locations) securely.
        """
        # 1. Identify Text Columns
        text_cols = df.select_dtypes(include=['object', 'category']).columns
        
        forward_map = {}
        reverse_map = {}
        shadow_df = df.copy()
        
        # KEYWORDS TO SKIP (Context, Notes, Descriptions)
        # These columns usually contain sentences, not specific entities to hide.
        skip_keywords = ['desc', 'note', 'comment', 'summary', 'text', 'content', 'review']
        
        print(f"⚡ [VAULT] Scanning {len(text_cols)} text columns for sensitive data...")

        for col in text_cols:
            # RULE 1: Skip Context Columns (e.g. "Product Description")
            if any(k in col.lower() for k in skip_keywords):
                print(f"   -> Skipping Context Column: {col}")
                continue

            # RULE 2: Skip Long Text (Likely Sentences)
            # If average length is > 40 chars, it's a sentence, not an ID.
            avg_len = df[col].astype(str).map(len).mean()
            if avg_len > 40: 
                print(f"   -> Skipping Long Text Column: {col} (Avg Len: {avg_len:.1f})")
                continue

            # --- TOKENIZATION (Universal) ---
            unique_vals = df[col].dropna().unique()
            col_map = {} 
            
            # Create a generic prefix from the column name (e.g. 'PatientID' -> 'PATI')
            clean_col = re.sub(r'\W+', '', col).upper()[:4]
            
            for i, val in enumerate(unique_vals):
                val_str = str(val).strip()
                
                # CRITICAL FIX: Ignore very short values (e.g. "A", "B", "1")
                # This prevents replacing every letter "a" in a sentence.
                if len(val_str) < 2: 
                    continue
                
                # Create Token (e.g., <PATI_1>, <COUN_5>)
                token = f"<{clean_col}_{i}>"
                
                # Store Map (Lower case for robust matching)
                forward_map[val_str.lower()] = token
                reverse_map[token] = val_str
                col_map[val] = token
            
            # Apply Vectorized Map to DataFrame
            if col_map:
                shadow_df[col] = shadow_df[col].map(col_map).fillna(shadow_df[col])

        # 3. Save Map to MongoDB
        if self.db is not None:
            self.db.vault_mappings.update_one(
                {"session_id": session_id},
                {"$set": {
                    "session_id": session_id,
                    "forward": forward_map, 
                    "reverse": reverse_map
                }},
                upsert=True
            )
            
        print(f"✅ [VAULT] Indexed {len(forward_map)} sensitive entities.")
        return shadow_df

    def protect(self, text: str, session_id: str = None):
        """
        Replaces Real Values -> Tokens safely.
        Uses Regex Boundaries (\b) to prevent corrupting words.
        """
        if not text: return "", 100

        # Load Map
        forward_map, _ = self._get_map(session_id)
        if not forward_map: 
            return text, 50 

        # Sort by length (Longest first) to match "New York" before "New"
        sorted_keys = sorted(forward_map.keys(), key=len, reverse=True)
        safe_text = text # Keep original casing for output, but search lower
        
        replaced_count = 0
        
        for key in sorted_keys:
            # REGEX FIX: \b ensures we match WHOLE WORDS only.
            # This fixes "records" -> "recor<TOKEN>s" bug.
            # re.escape(key) handles special chars like brackets or dots safely.
            pattern = r'\b' + re.escape(key) + r'\b'
            
            if re.search(pattern, safe_text, re.IGNORECASE):
                token = forward_map[key]
                # Replace with token, preserving surrounding text
                safe_text = re.sub(pattern, token, safe_text, flags=re.IGNORECASE)
                replaced_count += 1
                
        score = 100 if replaced_count > 0 else 80
        return safe_text, score

    def restore(self, text: str, session_id: str = None):
        """
        Replaces Tokens -> Real Values in the AI response.
        """
        if not text: return ""
        
        _, reverse_map = self._get_map(session_id)
        if not reverse_map: return text
        
        restored_text = text
        for token, original in reverse_map.items():
            if token in restored_text:
                restored_text = restored_text.replace(token, original)
                
        return restored_text