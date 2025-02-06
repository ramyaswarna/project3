# import pymongo
# import os
# import pdfplumber # PyMuPDF for text extraction
# from model_loader import ModelLoader
# from dotenv import load_dotenv
# from bson import ObjectId  # Import ObjectId from bson

# load_dotenv()

# class Database:
#     def __init__(self):
#         self.client = pymongo.MongoClient(os.getenv("MONGO_URI"))
#         self.db = self.client["AETNA_POLICY_DB"]
#         self.collection = self.db["AETNA_POLICY_DOCS"]
#         self.model_loader = ModelLoader()  

#     def chunk_text(self, text, chunk_size=300):  
#         """Splits text into smaller chunks for embedding"""
#         words = text.split()
#         return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

#     def store_vector(self, title, content):
#         """Stores extracted text in MongoDB using OpenAI embeddings, with chunking"""
#         chunks = self.chunk_text(content, chunk_size=300)  

#         for i, chunk in enumerate(chunks):
#             title_embedding = self.model_loader.generate_embedding(chunk)

#             if title_embedding is None or len(title_embedding) != 1536:
#                 print(f"Embedding failed for chunk {i}. Skipping.")
#                 continue

#             document = {
#                 "title": f"{title} - Chunk {i+1}",
#                 "content": chunk,
#                 "title_embedding": title_embedding
#             }
#             doc_id = self.collection.insert_one(document).inserted_id
#             print(f"Stored chunk {i+1} with ID: {doc_id}")

#     def query_database(self, query_text):
#         """Retrieves relevant document chunks using vector search"""
#         query_embedding = self.model_loader.generate_embedding(query_text)

#         if query_embedding is None or len(query_embedding) != 1536:
#             print("Failed to generate query embedding.")
#             return []

#         # print("Query Embedding:", query_embedding[:5])  # Debugging first 5 dimensions

#         results = self.collection.aggregate([
#             {
#                 "$vectorSearch": {
#                     "index": "vector_index_007",
#                     "path": "title_embedding",
#                     "queryVector": query_embedding,
#                     "numCandidates": 500,  
#                     "limit": 5  
#                 }
#             },
#             {"$project": {"_id": 1, "title": 1, "content": 1}}
#         ])

#         results_list = []
#         for result in results:
#             result["_id"] = str(result["_id"])  
#             results_list.append(result)

#         return results_list
import pymongo
import os
import pdfplumber  # PyMuPDF alternative for text extraction
from model_loader import ModelLoader
from dotenv import load_dotenv
from bson import ObjectId  # Import ObjectId from bson

load_dotenv()

# ✅ Fix: Create MongoDB connection per request
def get_database():
    """Creates a new MongoDB client per request to avoid fork issues."""
    client = pymongo.MongoClient(os.getenv("MONGO_URI"))
    return client["AETNA_POLICY_DB"]

class Database:
    def __init__(self):
        self.model_loader = ModelLoader()

    def chunk_text(self, text, chunk_size=300):
        """Splits text into smaller chunks for embedding"""
        words = text.split()
        return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

    def store_vector(self, title, content):
        """Stores extracted text in MongoDB using OpenAI embeddings, with chunking"""
        db = get_database()  # ✅ Create new MongoDB connection
        collection = db["AETNA_POLICY_DOCS"]

        chunks = self.chunk_text(content, chunk_size=300)

        for i, chunk in enumerate(chunks):
            title_embedding = self.model_loader.generate_embedding(chunk)

            if title_embedding is None or len(title_embedding) != 1536:
                print(f"Embedding failed for chunk {i}. Skipping.")
                continue

            document = {
                "title": f"{title} - Chunk {i+1}",
                "content": chunk,
                "title_embedding": title_embedding
            }
            doc_id = collection.insert_one(document).inserted_id
            print(f"Stored chunk {i+1} with ID: {doc_id}")

    def query_database(self, query_text):
        """Retrieves relevant document chunks using vector search"""
        db = get_database()  # ✅ Create new MongoDB connection
        collection = db["AETNA_POLICY_DOCS"]

        query_embedding = self.model_loader.generate_embedding(query_text)

        if query_embedding is None or len(query_embedding) != 1536:
            print("Failed to generate query embedding.")
            return []

        results = collection.aggregate([
            {
                "$vectorSearch": {
                    "index": "vector_index_007",
                    "path": "title_embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 500,
                    "limit": 5
                }
            },
            {"$project": {"_id": 1, "title": 1, "content": 1}}
        ])

        results_list = []
        for result in results:
            result["_id"] = str(result["_id"])
            results_list.append(result)

        return results_list
