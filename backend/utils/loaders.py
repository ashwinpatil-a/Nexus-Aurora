import pandas as pd
import io
import logging
# You need to install these: pip install pypdf openpyxl pyarrow
from pypdf import PdfReader 

def load_file_universally(filename: str, file_bytes: bytes):
    """
    Universal File Ingestion:
    - CSV/JSON/Excel/Parquet -> Returns (Pandas DataFrame, "structured")
    - PDF/TXT/MD -> Returns (String Text, "unstructured")
    """
    filename = filename.lower()
    
    try:
        # 1. Structured Data (Rows & Columns)
        if filename.endswith('.csv'):
            return pd.read_csv(io.BytesIO(file_bytes)), "structured"
            
        elif filename.endswith('.json'):
            return pd.read_json(io.BytesIO(file_bytes)), "structured"
            
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            return pd.read_excel(io.BytesIO(file_bytes)), "structured"

        elif filename.endswith('.parquet'):
            return pd.read_parquet(io.BytesIO(file_bytes)), "structured"

        # 2. Unstructured Data (Documents)
        elif filename.endswith('.pdf'):
            # Extract text from PDF
            reader = PdfReader(io.BytesIO(file_bytes))
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            return text, "unstructured"

        elif filename.endswith('.txt') or filename.endswith('.md'):
            return file_bytes.decode('utf-8', errors='ignore'), "unstructured"

        else:
            return None, "unsupported"

    except Exception as e:
        print(f"❌ Loader Failed: {e}")
        return None, "error"