from fastapi import APIRouter, Body, HTTPException
from db.mongo import db
from datetime import datetime
from ws.manager import manager
from cryptography.fernet import Fernet
import base64
from bson import ObjectId

message_router = APIRouter()
messages_collection = db["messages"]
connections_collection = db["connections"]
users_collection = db["users"]

# 👉 Password to Fernet key
def generate_fernet_key(password: str) -> bytes:
    padded = password.ljust(32, "0")
    return base64.urlsafe_b64encode(padded.encode())

# 👉 Get user by ObjectId
def get_user(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# ✅ Send encrypted message











@message_router.post("/send")
async def send_message(
    sender_id: str = Body(...),
    receiver_id: str = Body(...),
    message: str = Body(...)
):
    if not ObjectId.is_valid(sender_id) or not ObjectId.is_valid(receiver_id):
        raise HTTPException(status_code=400, detail="Invalid sender or receiver ID")

    connection = connections_collection.find_one({
        "$or": [
            {"sender_id": sender_id, "receiver_id": receiver_id},
            {"sender_id": receiver_id, "receiver_id": sender_id}
        ],
        "status": "accepted"
    })
    if not connection:
        raise HTTPException(status_code=403, detail="Connection not accepted by the user")

    sender_user = get_user(sender_id)
    receiver_user = get_user(receiver_id)

    if "raw_encryption_password" not in sender_user or "raw_encryption_password" not in receiver_user:
        raise HTTPException(status_code=400, detail="One or both users have no encryption password set.")

    sender_fernet = Fernet(generate_fernet_key(sender_user["raw_encryption_password"]))
    receiver_fernet = Fernet(generate_fernet_key(receiver_user["raw_encryption_password"]))

    encrypted_for_sender = sender_fernet.encrypt(message.encode()).decode()
    encrypted_for_receiver = receiver_fernet.encrypt(message.encode()).decode()

    result = messages_collection.insert_one({
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "message_for_sender": encrypted_for_sender,
        "message_for_receiver": encrypted_for_receiver,
        "timestamp": datetime.utcnow()
    })

    avatar_url = f"https://api.dicebear.com/8.x/adventurer/svg?seed={encrypted_for_receiver}"
    await manager.send_personal_message(
        avatar_url,
        receiver_id
    )

    return {"status": "Encrypted message sent", "message_id": str(result.inserted_id)}


















# ✅ Fetch encrypted messages
@message_router.post("/receive")
def receive_encrypted_messages(receiver_id: str = Body(...)):
    if not ObjectId.is_valid(receiver_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    messages_cursor = messages_collection.find({"receiver_id": receiver_id})
    messages = list(messages_cursor)

    if not messages:
        return {"received_messages": [], "info": "No messages found."}

    result = []
    for msg in messages:
        encrypted = msg.get("message_for_receiver", "")
        avatar_url = f"https://api.dicebear.com/8.x/adventurer/svg?seed={encrypted}"
        result.append({
            "message_id": str(msg["_id"]),
            "sender_id": msg["sender_id"],
            "encrypted_message": encrypted,
            "avatar_url": avatar_url,
            "timestamp": msg["timestamp"]
        })

    return {"received_messages": result}













@message_router.post("/decrypt")
def decrypt_message(
    message_id: str = Body(...),
    password: str = Body(...),
    user_id: str = Body(...)
):
    # Validate IDs
    if not ObjectId.is_valid(message_id) or not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid message ID or user ID")

    # Fetch message
    msg = messages_collection.find_one({"_id": ObjectId(message_id)})
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found.")

    # Fetch user attempting to decrypt
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user or "raw_encryption_password" not in user:
        raise HTTPException(status_code=403, detail="User not authorized or no password set.")

    # Check if password matches
    if password != user["raw_encryption_password"]:
        raise HTTPException(status_code=403, detail="Invalid password.")

    # Determine the correct encrypted field to decrypt
    fernet = Fernet(generate_fernet_key(password))

    try:
        if user_id == msg["sender_id"]:
            encrypted_data = msg.get("message_for_sender")
            if not encrypted_data:
                raise HTTPException(status_code=404, detail="Sender message not found.")
        elif user_id == msg["receiver_id"]:
            encrypted_data = msg.get("message_for_receiver")
            if not encrypted_data:
                raise HTTPException(status_code=404, detail="Receiver message not found.")
        else:
            raise HTTPException(status_code=403, detail="User not authorized for this message.")

        # Attempt decryption
        decrypted = fernet.decrypt(encrypted_data.encode()).decode()

        return {
            "sender_id": msg["sender_id"],
            "receiver_id": msg["receiver_id"],
            "original_message": decrypted,
            "timestamp": msg["timestamp"]
        }

    except Exception:
        raise HTTPException(status_code=403, detail="Decryption failed.")






async def store_encrypted_message(sender_id: str, receiver_id: str, message: str):
    if not ObjectId.is_valid(sender_id) or not ObjectId.is_valid(receiver_id):
        return

    connection = connections_collection.find_one({
        "$or": [
            {"sender_id": sender_id, "receiver_id": receiver_id},
            {"sender_id": receiver_id, "receiver_id": sender_id}
        ],
        "status": "accepted"
    })
    if not connection:
        return

    sender_user = get_user(sender_id)
    receiver_user = get_user(receiver_id)
    if "raw_encryption_password" not in sender_user or "raw_encryption_password" not in receiver_user:
        return

    sender_key = generate_fernet_key(sender_user["raw_encryption_password"])
    receiver_key = generate_fernet_key(receiver_user["raw_encryption_password"])

    encrypted_for_sender = Fernet(sender_key).encrypt(message.encode()).decode()
    encrypted_for_receiver = Fernet(receiver_key).encrypt(message.encode()).decode()

    messages_collection.insert_one({
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "message_for_sender": encrypted_for_sender,
        "message_for_receiver": encrypted_for_receiver,
        "timestamp": datetime.utcnow()
    })

    await manager.send_personal_message(
        f"Encrypted from {sender_id}: {encrypted_for_receiver}",
        receiver_id
    )






















@message_router.post("/conversation")
def get_conversation(user1_id: str = Body(...), user2_id: str = Body(...)):
    if not ObjectId.is_valid(user1_id) or not ObjectId.is_valid(user2_id):
        raise HTTPException(status_code=400, detail="Invalid user IDs")

    messages_cursor = messages_collection.find({
        "$or": [
            {"sender_id": user1_id, "receiver_id": user2_id},
            {"sender_id": user2_id, "receiver_id": user1_id}
        ]
    }).sort("timestamp", 1)

    result = []
    for msg in messages_cursor:
        avatar_sender = f"https://api.dicebear.com/8.x/adventurer/svg?seed={msg.get('message_for_sender', '')}"
        avatar_receiver = f"https://api.dicebear.com/8.x/adventurer/svg?seed={msg.get('message_for_receiver', '')}"
        result.append({
            "message_id": str(msg["_id"]),
            "sender_id": msg["sender_id"],
            "receiver_id": msg["receiver_id"],
            "message_for_sender": msg.get("message_for_sender", ""),
            "message_for_receiver": msg.get("message_for_receiver", ""),
            "avatar_sender": avatar_sender,
            "avatar_receiver": avatar_receiver,
            "timestamp": msg["timestamp"]
        })

    return {"conversation": result}















@message_router.post("/chat-partners")
def get_chat_partners(user_id: str = Body(...)):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    # Get all unique user IDs that this user has communicated with
    pipeline = [
        {
            "$match": {
                "$or": [
                    {"sender_id": user_id},
                    {"receiver_id": user_id}
                ]
            }
        },
        {
            "$project": {
                "other_user_id": {
                    "$cond": [
                        {"$eq": ["$sender_id", user_id]},
                        "$receiver_id",
                        "$sender_id"
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$other_user_id"
            }
        }
    ]

    partner_ids_cursor = messages_collection.aggregate(pipeline)
    partner_ids = [entry["_id"] for entry in partner_ids_cursor]

    if not partner_ids:
        return {"chat_partners": [], "info": "No chat partners found."}

    users_cursor = users_collection.find({"_id": {"$in": [ObjectId(uid) for uid in partner_ids]}})
    chat_partners = []

    for user in users_cursor:
        # Avatar generated from their _id or email
        seed = user.get("username", str(user["_id"]))
        avatar_url = f"https://api.dicebear.com/8.x/adventurer/svg?seed={seed}"
        chat_partners.append({
            "user_id": str(user["_id"]),
            "username": user.get("username", ""),
            "email": user.get("email", ""),
            "avatar": avatar_url
        })

    return {"chat_partners": chat_partners}












