import os
import uvicorn
import jwt
import secrets
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from webauthn import verify_registration_response, verify_authentication_response
from pydantic import BaseModel
from typing import Dict
from datetime import datetime, timedelta
from fastapi.responses import HTMLResponse

# Get PORT from environment (Render provides this dynamically)
port = int(os.getenv("PORT", "8000"))

# Initialize FastAPI app
app = FastAPI()
security = HTTPBearer()

# ✅ **JWT Configuration**
SECRET_KEY = os.environ.get("SECRET_KEY", "your_secret_key")  # Secure storage of secret key
ALGORITHM = "HS256"

# ✅ **In-memory database for face authentication**
users_db: Dict[str, str] = {}
challenges: Dict[str, str] = {}  # Store generated challenges per user

# ✅ **Pydantic model for WebAuthn authentication**
class FaceAuthRequest(BaseModel):
    credential: dict

# ✅ **1️⃣ Face Registration Route**
@app.post("/register-face")
def register_face(request: FaceAuthRequest):
    try:
        user_id = "user@example.com"
        expected_challenge = challenges.pop(user_id, None)  # Get and remove challenge

        if not expected_challenge:
            raise HTTPException(status_code=400, detail="No challenge found for this user")

        credential_data = verify_registration_response(
            credential=request.credential,
            expected_challenge=expected_challenge,
            expected_rp_id="ai-auth.onrender.com"
        )

        # ✅ Save user and credential ID
        users_db[user_id] = credential_data.credential_id
        return {"message": "Face authentication successfully registered!"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ✅ **2️⃣ Face Verification Route**
@app.post("/verify-face")
def verify_face(request: FaceAuthRequest):
    try:
        user_id = "user@example.com"
        credential_id = users_db.get(user_id)

        if not credential_id:
            raise HTTPException(status_code=401, detail="No registration found")

        expected_challenge = challenges.pop(user_id, None)  # Get and remove challenge
        if not expected_challenge:
            raise HTTPException(status_code=401, detail="No challenge found for this user")

        verify_authentication_response(
            credential=request.credential,
            expected_challenge=expected_challenge,
            expected_rp_id="ai-auth.onrender.com",
            credential_id=credential_id
        )

        # ✅ Generate JWT token
        token = generate_jwt(user_id)
        return {"message": "Face verification successful!", "token": token}

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# ✅ **3️⃣ JWT Token Generation**
def generate_jwt(email: str):
    expiration = datetime.utcnow() + timedelta(hours=2)
    payload = {"sub": email, "exp": expiration}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# ✅ **4️⃣ Generate Challenge**
@app.get("/generate-challenge")
def generate_challenge():
    user_id = "user@example.com"
    challenge = secrets.token_urlsafe(32)  # Secure random challenge
    challenges[user_id] = challenge
    return {"challenge": challenge}

# ✅ **5️⃣ Protected Route**
@app.get("/protected")
def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"message": "Access granted!", "user": payload["sub"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ✅ **6️⃣ Health Check Route for Render**
@app.get("/", response_class=HTMLResponse)
def home():
    return "<h1>AI Authentication API is Live 🚀</h1>"

# ✅ **7️⃣ Correct Port Binding for Render**
if __name__ == "__main__":
    print(f"Starting server on port {port}...")  # Debugging line
    uvicorn.run(app, host="0.0.0.0", port=port)
