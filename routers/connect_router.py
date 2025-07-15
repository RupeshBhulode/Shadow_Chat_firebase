#ConnectRouter
from fastapi import APIRouter, Body, Query, HTTPException
from db.firebase import users_collection, firestore_db as db
from google.cloud.firestore_v1 import DocumentSnapshot
from datetime import datetime

connect_router = APIRouter()
connections_collection = db.collection("connections")

def get_user_by_id(user_id: str):
    doc = users_collection.document(user_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    return doc.to_dict() | {"user_id": doc.id}

@connect_router.post("/send-request")
def send_request(sender_id: str = Body(...), receiver_id: str = Body(...)):
    sender = get_user_by_id(sender_id)
    receiver = get_user_by_id(receiver_id)

    existing = connections_collection.where("sender_id", "==", sender_id).where("receiver_id", "==", receiver_id).get()
    if existing:
        return {"message": "Request already sent or already connected"}

    connections_collection.add({
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "status": "pending",
        "created_at": datetime.utcnow()
    })

    return {"message": "Connection request sent", "status": "pending"}

@connect_router.post("/accept-request")
def accept_request(sender_id: str = Body(...), receiver_id: str = Body(...)):
    pending_requests = connections_collection.where("sender_id", "==", sender_id).where("receiver_id", "==", receiver_id).where("status", "==", "pending").get()

    if not pending_requests:
        return {"error": "No pending request found"}

    for doc in pending_requests:
        connections_collection.document(doc.id).update({"status": "accepted"})

    return {"message": "Connection accepted"}

@connect_router.get("/list")
def get_connections(user_id: str = Query(...)):
    connections = connections_collection.where("status", "==", "accepted").get()

    connected_users = []
    for conn in connections:
        data = conn.to_dict()
        if data["sender_id"] == user_id or data["receiver_id"] == user_id:
            other_id = data["receiver_id"] if data["sender_id"] == user_id else data["sender_id"]
            user = get_user_by_id(other_id)
            connected_users.append({
                "user_id": user["user_id"],
                "username": user.get("username", "N/A"),
                "email": user["email"]
            })

    return {"connections": connected_users}

@connect_router.get("/users/all")
def get_all_users():
    users = users_collection.stream()
    result = []
    for doc in users:
        user = doc.to_dict()
        result.append({
            "user_id": doc.id,
            "username": user.get("username", "N/A"),
            "email": user["email"],
            "avatar": user.get("avatar", "")
        })
    return {"users": result}

@connect_router.get("/check-status")
def check_connection_status(sender_id: str = Query(...), receiver_id: str = Query(...)):
    requests = connections_collection.where("sender_id", "in", [sender_id, receiver_id])\
        .where("receiver_id", "in", [sender_id, receiver_id]).get()

    for req in requests:
        return {"status": req.to_dict().get("status", "none")}

    return {"status": "none"}

@connect_router.get("/sent-requests")
def get_sent_requests(user_id: str = Query(...)):
    sent_requests = connections_collection.where("sender_id", "==", user_id).get()
    result = []
    for req in sent_requests:
        data = req.to_dict()
        receiver = get_user_by_id(data["receiver_id"])
        result.append({
            "user_id": receiver["user_id"],
            "username": receiver.get("username", "N/A"),
            "email": receiver["email"],
            "avatar": receiver.get("avatar", ""),
            "status": 1 if data["status"] == "accepted" else 0
        })
    return {"sent_requests": result}

@connect_router.get("/received-requests")
def get_received_requests(user_id: str = Query(...)):
    received_requests = connections_collection.where("receiver_id", "==", user_id).get()
    result = []
    for req in received_requests:
        data = req.to_dict()
        sender = get_user_by_id(data["sender_id"])
        result.append({
            "user_id": sender["user_id"],
            "username": sender.get("username", "N/A"),
            "email": sender["email"],
            "avatar": sender.get("avatar", ""),
            "status": 2 if data["status"] == "accepted" else 3
        })
    return {"received_requests": result}
