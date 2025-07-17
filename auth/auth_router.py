from fastapi import APIRouter, HTTPException
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
    id_token: str  # Firebase Auth ID token from frontend


@auth_router.post("/register")
async def register(user: UserProfile):
    # ✅ Verify the Firebase ID token
    try:
        decoded_token = firebase_auth.verify_id_token(user.id_token)  # ✅ fixed
        uid = decoded_token["uid"]
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")

    # ✅ Check if profile already exists
    existing_doc = users_collection.document(uid).get()
    if existing_doc.exists:
        raise HTTPException(status_code=400, detail="User already exists")

    # ✅ Save profile
    avatar_url = user.avatar or f"https://api.dicebear.com/8.x/adventurer/svg?seed={user.username}"
    users_collection.document(uid).set({
        "username": user.username,
        "email": user.email,
        "avatar": avatar_url
    })

    # ✅ Optional custom access token (JWT)
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
        decoded_token = firebase_auth.verify_id_token(data.id_token)  # ✅ fixed
        uid = decoded_token["uid"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")

    # ✅ Get profile
    user_doc = users_collection.document(uid).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User profile not found")

    profile = user_doc.to_dict()

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

