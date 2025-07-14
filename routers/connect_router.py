from fastapi import APIRouter, Body, Query, HTTPException
from db.mongo import users_collection, db
from bson import ObjectId
from datetime import datetime

connect_router = APIRouter()
connections_collection = db["connections"]

def get_user_by_id(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@connect_router.post("/send-request")
def send_request(sender_id: str = Body(...), receiver_id: str = Body(...)):
    sender = get_user_by_id(sender_id)
    receiver = get_user_by_id(receiver_id)

    existing = connections_collection.find_one({
        "sender_id": sender_id,
        "receiver_id": receiver_id
    })

    if existing:
        return {"message": "Request already sent or already connected"}

    connections_collection.insert_one({
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "status": "pending",
        "created_at": datetime.utcnow()
    })

    return {"message": "Connection request sent", "status": "pending"}

@connect_router.post("/accept-request")
def accept_request(sender_id: str = Body(...), receiver_id: str = Body(...)):
    connection = connections_collection.find_one({
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "status": "pending"
    })

    if not connection:
        return {"error": "No pending request found"}

    connections_collection.update_one(
        {"_id": connection["_id"]},
        {"$set": {"status": "accepted"}}
    )

    return {"message": "Connection accepted"}

@connect_router.get("/list")
def get_connections(user_id: str = Query(...)):
    accepted_connections = connections_collection.find({
        "$or": [
            {"sender_id": user_id, "status": "accepted"},
            {"receiver_id": user_id, "status": "accepted"}
        ]
    })

    connected_users = []
    for conn in accepted_connections:
        other_id = conn["receiver_id"] if conn["sender_id"] == user_id else conn["sender_id"]
        user = get_user_by_id(other_id)
        connected_users.append({
            "user_id": str(user["_id"]),
            "username": user.get("username", "N/A"),
            "email": user["email"]
        })

    return {"connections": connected_users}

@connect_router.get("/users/all")
def get_all_users():
    users = users_collection.find()
    result = []
    for user in users:
        result.append({
            "user_id": str(user["_id"]),
            "username": user.get("username", "N/A"),
            "email": user["email"],
            "avatar": user.get("avatar", "")
        })
    return {"users": result}

@connect_router.get("/check-status")
def check_connection_status(sender_id: str = Query(...), receiver_id: str = Query(...)):
    existing = connections_collection.find_one({
        "$or": [
            {"sender_id": sender_id, "receiver_id": receiver_id},
            {"sender_id": receiver_id, "receiver_id": sender_id}
        ]
    })

    if not existing:
        return {"status": "none"}

    return {"status": existing["status"]}

@connect_router.get("/sent-requests")
def get_sent_requests(user_id: str = Query(...)):
    sent_requests = connections_collection.find({
        "sender_id": user_id
    })

    result = []
    for req in sent_requests:
        receiver = get_user_by_id(req["receiver_id"])
        result.append({
            "user_id": str(receiver["_id"]),
            "username": receiver.get("username", "N/A"),
            "email": receiver["email"],
            "avatar": receiver.get("avatar", ""),
            "status": 1 if req["status"] == "accepted" else 0
        })

    return {"sent_requests": result}

@connect_router.get("/received-requests")
def get_received_requests(user_id: str = Query(...)):
    received_requests = connections_collection.find({
        "receiver_id": user_id
    })

    result = []
    for req in received_requests:
        sender = get_user_by_id(req["sender_id"])
        result.append({
            "user_id": str(sender["_id"]),
            "username": sender.get("username", "N/A"),
            "email": sender["email"],
            "avatar": sender.get("avatar", ""),
            "status": 2 if req["status"] == "accepted" else 3
        })

    return {"received_requests": result}
