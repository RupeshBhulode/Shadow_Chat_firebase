from fastapi import APIRouter, Body, HTTPException
from db.firebase import firestore_db  # 🔁 Use Firebase instead of MongoDB
from datetime import datetime
from ws.manager import manager
from cryptography.fernet import Fernet
import base64

message_router = APIRouter()

# Firestore collections
messages_collection = firestore_db.collection("messages")
connections_collection = firestore_db.collection("connections")
users_collection = firestore_db.collection("users")

# 👉 Password to Fernet key
def generate_fernet_key(password: str) -> bytes:
    padded = password.ljust(32, "0")
    return base64.urlsafe_b64encode(padded.encode())

# 👉 Get user by Firestore ID
def get_user(user_id: str):
    doc = users_collection.document(user_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    return doc.to_dict()







@message_router.post("/send")
async def send_message(
    sender_id: str = Body(...),
    receiver_id: str = Body(...),
    message: str = Body(...)
):
    # Firestore uses string IDs, no ObjectId check needed
    # 🔁 Check if a valid connection exists
    connection_query = connections_collection.where("status", "==", "accepted").where(
        "sender_id", "in", [sender_id, receiver_id]
    ).where(
        "receiver_id", "in", [sender_id, receiver_id]
    ).stream()

    connection = next(connection_query, None)
    if not connection:
        raise HTTPException(status_code=403, detail="Connection not accepted by the user")

    # 🔁 Fetch user documents from Firestore
    sender_user = get_user(sender_id)
    receiver_user = get_user(receiver_id)

    if "raw_encryption_password" not in sender_user or "raw_encryption_password" not in receiver_user:
        raise HTTPException(status_code=400, detail="One or both users have no encryption password set.")

    # 🔐 Encrypt message using sender and receiver passwords
    sender_fernet = Fernet(generate_fernet_key(sender_user["raw_encryption_password"]))
    receiver_fernet = Fernet(generate_fernet_key(receiver_user["raw_encryption_password"]))

    encrypted_for_sender = sender_fernet.encrypt(message.encode()).decode()
    encrypted_for_receiver = receiver_fernet.encrypt(message.encode()).decode()

    # 📩 Store message in Firestore
    doc_ref = messages_collection.document()
    doc_ref.set({
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "message_for_sender": encrypted_for_sender,
        "message_for_receiver": encrypted_for_receiver,
        "timestamp": datetime.utcnow()
    })

    # 🔔 Notify receiver via WebSocket
    avatar_url = f"https://api.dicebear.com/8.x/adventurer/svg?seed={encrypted_for_receiver}"
    await manager.send_personal_message(avatar_url, receiver_id)

    return {"status": "Encrypted message sent", "message_id": doc_ref.id}












@message_router.post("/receive")
def receive_encrypted_messages(receiver_id: str = Body(...)):
    # 🔍 Fetch all messages where this user is the receiver
    messages_query = messages_collection.where("receiver_id", "==", receiver_id).stream()
    messages = list(messages_query)

    if not messages:
        return {"received_messages": [], "info": "No messages found."}

    result = []
    for msg in messages:
        msg_data = msg.to_dict()
        encrypted = msg_data.get("message_for_receiver", "")
        avatar_url = f"https://api.dicebear.com/8.x/adventurer/svg?seed={encrypted}"
        result.append({
            "message_id": msg.id,
            "sender_id": msg_data["sender_id"],
            "encrypted_message": encrypted,
            "avatar_url": avatar_url,
            "timestamp": msg_data.get("timestamp")
        })

    return {"received_messages": result}









@message_router.post("/decrypt")
def decrypt_message(
    message_id: str = Body(...),
    password: str = Body(...),
    user_id: str = Body(...)
):
    # 🔍 Fetch message document from Firestore
    msg_ref = messages_collection.document(message_id)
    msg_snapshot = msg_ref.get()
    if not msg_snapshot.exists:
        raise HTTPException(status_code=404, detail="Message not found.")
    msg = msg_snapshot.to_dict()

    # 🔍 Fetch user document
    user_doc = users_collection.document(user_id).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found.")
    user = user_doc.to_dict()

    # 🚫 Ensure password field exists
    if "raw_encryption_password" not in user:
        raise HTTPException(status_code=403, detail="User has no encryption password set.")

    # 🔐 Check password match
    if password != user["raw_encryption_password"]:
        raise HTTPException(status_code=403, detail="Invalid password.")

    # 🔑 Generate key and decrypt
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
    # ⚠️ Firestore uses string IDs, no need for ObjectId validation
    connection_query = connections_collection.where("status", "==", "accepted").where("sender_id", "in", [sender_id, receiver_id]).where("receiver_id", "in", [sender_id, receiver_id]).stream()
    connection = next(connection_query, None)
    if not connection:
        return

    sender_doc = users_collection.document(sender_id).get()
    receiver_doc = users_collection.document(receiver_id).get()

    if not sender_doc.exists or not receiver_doc.exists:
        return

    sender_user = sender_doc.to_dict()
    receiver_user = receiver_doc.to_dict()

    if "raw_encryption_password" not in sender_user or "raw_encryption_password" not in receiver_user:
        return

    sender_key = generate_fernet_key(sender_user["raw_encryption_password"])
    receiver_key = generate_fernet_key(receiver_user["raw_encryption_password"])

    encrypted_for_sender = Fernet(sender_key).encrypt(message.encode()).decode()
    encrypted_for_receiver = Fernet(receiver_key).encrypt(message.encode()).decode()

    await messages_collection.add({
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
    # Firestore doesn't require ObjectId validation
    messages_query = messages_collection.where("sender_id", "in", [user1_id, user2_id])\
                                        .where("receiver_id", "in", [user1_id, user2_id])\
                                        .order_by("timestamp")
    messages_docs = messages_query.stream()

    result = []
    for doc in messages_docs:
        msg = doc.to_dict()
        avatar_sender = f"https://api.dicebear.com/8.x/adventurer/svg?seed={msg.get('message_for_sender', '')}"
        avatar_receiver = f"https://api.dicebear.com/8.x/adventurer/svg?seed={msg.get('message_for_receiver', '')}"
        result.append({
            "message_id": doc.id,
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
    # Fetch messages where user is sender or receiver
    messages_as_sender = messages_collection.where("sender_id", "==", user_id).stream()
    messages_as_receiver = messages_collection.where("receiver_id", "==", user_id).stream()

    partner_ids = set()

    for doc in messages_as_sender:
        data = doc.to_dict()
        partner_ids.add(data["receiver_id"])

    for doc in messages_as_receiver:
        data = doc.to_dict()
        partner_ids.add(data["sender_id"])

    if not partner_ids:
        return {"chat_partners": [], "info": "No chat partners found."}

    chat_partners = []
    for uid in partner_ids:
        user_doc = users_collection.document(uid).get()
        if user_doc.exists:
            user = user_doc.to_dict()
            seed = user.get("username", uid)
            avatar_url = f"https://api.dicebear.com/8.x/adventurer/svg?seed={seed}"
            chat_partners.append({
                "user_id": uid,
                "username": user.get("username", ""),
                "email": user.get("email", ""),
                "avatar": avatar_url
            })

    return {"chat_partners": chat_partners}


@message_router.get("/user-count")
def get_user_count():
    # 🔍 Fetch all users from Firestore
    users_stream = users_collection.stream()
    count = sum(1 for _ in users_stream)

    return {"total_users": count}









