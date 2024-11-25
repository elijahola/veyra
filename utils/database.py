from pymongo import MongoClient
import os

def get_db():
    client = MongoClient(os.getenv("MONGODB_URI"))
    return client["veyra"]
