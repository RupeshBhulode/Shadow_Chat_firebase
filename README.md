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











## 📝 Full Swagger Docs

Swagger UI available at:

🔗 **[http://localhost:8000/docs](http://localhost:8000/docs)**

Explore all routes and test APIs directly from the browser.

<img width="1802" height="760" alt="Screenshot (233)" src="https://github.com/user-attachments/assets/da613512-cef9-4c44-bc8e-6e58221ebbc3" />
<img width="1793" height="615" alt="Screenshot (234)" src="https://github.com/user-attachments/assets/87b8f6a2-e845-46fd-a6e7-58cceadf3b20" />


---

## 📦 Deployment

✅ **Deployed on Render**

You can also run it locally during development:

- The **Firebase database** remains the same across environments.
- No need to spin up separate DBs — just **plug and play**!

---

## 🔐 Security Notes

🛡️ **JWT-Based Authentication**  
- Access tokens are **securely stored** and **validated** on every protected route.
- Tokens expire after a configurable time (set via `.env` as `TOKEN_EXPIRE_MINUTES`).

🕵️‍♂️ **Message Protection & Encryption**
- Messages are **encrypted and hidden inside images** (*steganography*).
- Only the **sender** and **receiver** with the correct passcode can **decrypt** the hidden message.

🧱 **Access Control**
- Role-based guards prevent unauthorized access.
- **Admin**, **User**, and **Moderator** roles (customizable).
- Only allowed users can call sensitive routes like `/delete`, `/ban`, etc.

---

✅ Everything is handled securely and designed for scalability.








