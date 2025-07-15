import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("db/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

firestore_db = firestore.client()
users_collection = firestore_db.collection("users")

