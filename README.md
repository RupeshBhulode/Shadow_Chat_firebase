# ShadowChat – Backend API 🔐

ShadowChat is a secure, real-time messaging backend built using **FastAPI**, designed to support encrypted communications, role-based authentication, and invitation-based chat initiation.

This backend powers the ShadowChat frontend, handling authentication, session control, message encryption, and notification systems.

---

## 🛠 Tech Stack

- **FastAPI** – Modern, fast (high-performance) web framework for Python
- **Firebase Firestore** – Real-time NoSQL database
- **JWT (JSON Web Tokens)** – Token-based user authentication
- **Pillow (PIL)** – For image manipulation (used in message steganography)
- **Python-dotenv** – Manage environment variables
- **Uvicorn** – ASGI server for FastAPI

---

## 📁 Project Structure
<img width="508" height="838" alt="Screenshot 2025-07-21 121627" src="https://github.com/user-attachments/assets/0b6c0c26-c77d-4bf0-9eec-365733f7646a" />


---

## 🔐 Features

- JWT-based **authentication system**
- **Role-based access control** (User & Recruiter)
- **Encrypted messaging**, using a custom 2-digit passcode set by the user
- **Steganography-based message encryption** (messages hidden in images)
- **Invitation-based messaging access**
- Firebase integration for **real-time notifications**
- Password session management: set, update, validate
- Secure API routes for login, register, profile, and chat

---

## ⚙️ Setup Instructions

### 1. Clone the Repo
```bash
git clone https://github.com/yourusername/shadowchat-backend.git
cd shadowchat-backend
