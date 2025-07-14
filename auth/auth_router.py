from fastapi import APIRouter, HTTPException, status
from models.user import UserRegister, UserLogin
from db.mongo import users_collection
from auth.auth_handler import hash_password, verify_password, create_access_token

auth_router = APIRouter()

@auth_router.post("/register")
def register(user: UserRegister):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_pw = hash_password(user.password)
    avatar_url = f"https://api.dicebear.com/8.x/adventurer/svg?seed={user.username}"

    new_user = {
        "username": user.username,
        "email": user.email,
        "password": hashed_pw,
        "avatar": avatar_url
    }

    result = users_collection.insert_one(new_user)
    user_id = str(result.inserted_id)

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
def login(user: UserLogin):
    db_user = users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(db_user["_id"])})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": str(db_user["_id"]),
            "username": db_user.get("username", "N/A"),
            "email": db_user["email"],
            "avatar": db_user.get("avatar", "N/A")
        }
    }
