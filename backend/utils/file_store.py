import pickle
import bson.binary
import logging

class MongoFileStore:
    def __init__(self, db):
        self.db = db

    def save_file(self, session_id: str, data, data_type: str, filename: str):
        """
        Saves DataFrame or Text to MongoDB (Zero Local Storage).
        """
        if self.db is None: return False

        try:
            # Serialize Data
            if data_type == "structured":
                # Convert DataFrame to binary pickle to preserve data types
                content_binary = pickle.dumps(data)
            else:
                # Text is just encoded string
                content_binary = data.encode('utf-8')

            # Upsert into 'file_storage' collection
            self.db.file_storage.update_one(
                {"session_id": session_id},
                {"$set": {
                    "session_id": session_id,
                    "filename": filename,
                    "data_type": data_type,
                    "content": bson.binary.Binary(content_binary),
                    "updated_at": bson.datetime.datetime.now()
                }},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"❌ Mongo Save Error: {e}")
            return False

    def load_file(self, session_id: str):
        """
        Retrieves file from MongoDB and reconstructs it into RAM.
        """
        if self.db is None: return None, None

        doc = self.db.file_storage.find_one({"session_id": session_id})
        if not doc:
            return None, None

        try:
            data_type = doc["data_type"]
            content_binary = doc["content"]

            if data_type == "structured":
                data = pickle.loads(content_binary) # Reconstruct DataFrame
            else:
                data = content_binary.decode('utf-8') # Reconstruct Text

            return data, data_type
        except Exception as e:
            print(f"❌ Mongo Load Error: {e}")
            return None, None