from fastapi import FastAPI
from auth.auth_router import auth_router
from routers.connect_router import connect_router  # import the connect router
from ws.socket_router import socket_router
from routers.message_router import message_router
from routers.password_router import password_router
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_router, prefix="/auth")
app.include_router(connect_router, prefix="/connect")
app.include_router(socket_router)
app.include_router(message_router, prefix="/messages")
app.include_router(password_router)