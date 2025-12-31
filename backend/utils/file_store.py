# backend/utils/file_store.py
import pickle
import gridfs
from datetime import datetime

class MongoFileStore:
    def __init__(self, db):
        self.db = db
        if db is not None:
            self.fs = gridfs.GridFS(db)

    def save_file(self, session_id: str, data, data_type: str, filename: str):
        if self.db is None: return False
        try:
            # Cleanup old
            old = self.db.file_mappings.find_one({"session_id": session_id})
            if old: 
                try: self.fs.delete(old['file_id'])
                except: pass

            content = pickle.dumps(data) if data_type == "structured" else data.encode('utf-8')
            file_id = self.fs.put(content, filename=filename)

            self.db.file_mappings.update_one(
                {"session_id": session_id},
                {"$set": {"session_id": session_id, "filename": filename, "data_type": data_type, "file_id": file_id, "updated_at": datetime.now()}},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"❌ Save Error: {e}")
            return False

    def load_file(self, session_id: str):
        if self.db is None: return None, None
        try:
            mapping = self.db.file_mappings.find_one({"session_id": session_id})
            if not mapping: return None, None
            
            grid_out = self.fs.get(mapping['file_id'])
            content = grid_out.read()
            
            if mapping["data_type"] == "structured":
                return pickle.loads(content), "structured"
            return content.decode('utf-8'), "unstructured"
        except Exception as e:
            print(f"❌ Load Error: {e}")
            return None, None