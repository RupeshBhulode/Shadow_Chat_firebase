from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["shadowchat"]
users_collection = db["users"]
