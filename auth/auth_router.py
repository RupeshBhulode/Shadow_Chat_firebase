from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from db.firebase import users_collection
from auth.auth_handler import create_access_token
from firebase_admin import auth as firebase_auth

auth_router = APIRouter()

# Models
class UserProfile(BaseModel):
    username: str
    email: str
    avatar: str = None
    id_token: str  # comes from frontend Firebase Auth

@auth_router.post("/register")
async def register(user: UserProfile):
    # ✅ Verify the Firebase ID token from frontend
    try:
        decoded_token = auth_client.verify_id_token(user.id_token)
        uid = decoded_token["uid"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")

    # ✅ Check if profile already exists in Firestore
    existing_doc = users_collection.document(uid).get()
    if existing_doc.exists:
        raise HTTPException(status_code=400, detail="User already exists")

    # ✅ Store additional profile data in Firestore
    avatar_url = user.avatar or f"https://api.dicebear.com/8.x/adventurer/svg?seed={user.username}"
    users_collection.document(uid).set({
        "username": user.username,
        "email": user.email,
        "avatar": avatar_url
    })

    # ✅ Create your own access token if you want (optional)
    token = create_access_token({"sub": uid})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": uid,
            "username": user.username,
            "email": user.email,
            "avatar": avatar_url
        }
    }


class LoginData(BaseModel):
    id_token: str  # Firebase Auth token

@auth_router.post("/login")
async def login(data: LoginData):
    # ✅ Verify Firebase ID token
    try:
        decoded_token = auth_client.verify_id_token(data.id_token)
        uid = decoded_token["uid"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")

    # ✅ Get profile from Firestore
    user_doc = users_collection.document(uid).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User profile not found")

    profile = user_doc.to_dict()

    # ✅ Create your own access token if you want
    token = create_access_token({"sub": uid})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": uid,
            "username": profile.get("username"),
            "email": profile.get("email"),
            "avatar": profile.get("avatar")
        }
    }
