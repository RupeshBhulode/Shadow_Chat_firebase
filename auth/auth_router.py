#Auth router
from fastapi import APIRouter, HTTPException
from models.user import UserRegister, UserLogin
from db.firebase import users_collection  # 🔁 updated import
from auth.auth_handler import hash_password, verify_password, create_access_token

auth_router = APIRouter()

@auth_router.post("/register")
async def register(user: UserRegister):
    # 🔍 Check if email already exists
    existing_user = users_collection.where("email", "==", user.email).stream()
    if any(existing_user):
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_pw = hash_password(user.password)
    avatar_url = f"https://api.dicebear.com/8.x/adventurer/svg?seed={user.username}"

    new_user_data = {
        "username": user.username,
        "email": user.email,
        "password": hashed_pw,
        "avatar": avatar_url
    }

    # 🆕 Add new user to Firestore
    new_user_ref = users_collection.document()  # Auto-ID
    new_user_ref.set(new_user_data)
    user_id = new_user_ref.id

    token = create_access_token({"sub": user_id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user_id,
            "username": user.username,
            "email": user.email,
            "avatar": avatar_url
        }
    }


@auth_router.post("/login")
async def login(user: UserLogin):
    # 🔍 Look up user by email
    query = users_collection.where("email", "==", user.email).limit(1).stream()
    user_doc = next(query, None)

    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_data = user_doc.to_dict()

    if not verify_password(user.password, user_data["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user_doc.id})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user_doc.id,
            "username": user_data.get("username", "N/A"),
            "email": user_data["email"],
            "avatar": user_data.get("avatar", "N/A")
        }
    }
