import os
import json
import tempfile
import firebase_admin
from firebase_admin import credentials, firestore

# Read service account credentials from environment variable
firebase_creds = os.environ.get("FIREBASE_CREDENTIALS_JSON")
if not firebase_creds:
    raise RuntimeError("🔥 FIREBASE_CREDENTIALS_JSON not set in environment variables.")

# Parse JSON string to dict
cred_dict = json.loads(firebase_creds)

# ✅ Write the credentials to a temporary file
with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_json:
    json.dump(cred_dict, temp_json)
    temp_json.flush()
    cred = credentials.Certificate(temp_json.name)

# ✅ Initialize Firebase
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# ✅ Firestore client
firestore_db = firestore.client()
users_collection = firestore_db.collection("users")

