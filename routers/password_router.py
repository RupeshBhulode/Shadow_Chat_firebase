#Passord
from fastapi import APIRouter, Body, HTTPException
from db.firebase import users_collection  # Firestore users collection
import re

password_router = APIRouter()

def validate_password(password: str):
    # Exactly 2 digits
    if not re.fullmatch(r"\d{2}", password):
        raise HTTPException(status_code=400, detail="Password must be exactly 2 digits.")

def get_user_by_id(user_id: str):
    user_doc = users_collection.document(user_id).get()
    if not user_doc.exists:
        return None
    return user_doc.to_dict()

@password_router.post("/password/set")
def set_or_update_password(user_id: str = Body(...), password: str = Body(...)):
    validate_password(password)

    user_doc = users_collection.document(user_id).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found.")

    users_collection.document(user_id).update({
        "raw_encryption_password": password
    })
    return {"message": "Raw password set/updated successfully."}

@password_router.get("/password/get")
def get_raw_password(user_id: str):
    user_doc = users_collection.document(user_id).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found.")

    user = user_doc.to_dict()
    if "raw_encryption_password" not in user:
        raise HTTPException(status_code=404, detail="Password not set.")

    return {"user_id": user_id, "raw_password": user["raw_encryption_password"]}

