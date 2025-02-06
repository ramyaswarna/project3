from pymongo import MongoClient
import os

client = MongoClient(os.getenv("MONGO_URI"))
print(client.list_database_names())  # Should return database names
