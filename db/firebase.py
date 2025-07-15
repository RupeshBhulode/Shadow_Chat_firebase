import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Read service account credentials from environment variable
firebase_creds = os.environ.get("FIREBASE_CREDENTIALS_JSON")
if not firebase_creds:
    raise RuntimeError("🔥 FIREBASE_CREDENTIALS_JSON not set in environment variables.")

# Parse JSON string to dict
cred_dict = json.loads(firebase_creds)

# Initialize Firebase app with in‑memory credentials
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)

# Firestore client
firestore_db = firestore.client()
users_collection = firestore_db.collection("users")
