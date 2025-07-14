from fastapi import APIRouter, Body, HTTPException
from db.mongo import db
from bson import ObjectId
import re

password_router = APIRouter()
users_collection = db["users"]

def validate_password(password: str):
    # Exactly 2 digits
    if not re.fullmatch(r"\d{2}", password):
        raise HTTPException(status_code=400, detail="Password must be exactly 2 digits.")

def get_user_by_id(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    return user

@password_router.post("/password/set")
def set_or_update_password(user_id: str = Body(...), password: str = Body(...)):
    validate_password(password)

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"raw_encryption_password": password}}
    )
    return {"message": "Raw password set/updated successfully."}

@password_router.get("/password/get")
def get_raw_password(user_id: str):
    user = get_user_by_id(user_id)
    if not user or "raw_encryption_password" not in user:
        raise HTTPException(status_code=404, detail="Password not set.")
    return {"user_id": user_id, "raw_password": user["raw_encryption_password"]}
