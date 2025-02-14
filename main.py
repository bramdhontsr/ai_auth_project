import os
import uvicorn
import jwt
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from webauthn import verify_registration_response, verify_authentication_response
from pydantic import BaseModel
from typing import Dict
from datetime import datetime, timedelta

# Initialize FastAPI app
app = FastAPI()
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

# In-memory database for face authentication
users_db: Dict[str, str] = {}

# Pydantic model for WebAuthn authentication
class FaceAuthRequest(BaseModel):
    credential: dict

# ✅ **Face Registration Route**
@app.post("/register-face")
def register_face(request: FaceAuthRequest):
    try:
        credential_data = verify_registration_response(
            credential=request.credential,
            expected_challenge="123456",
            expected_rp_id="ai-auth.onrender.com"
        )

        # Save user and credential ID
        users_db["user@example.com"] = credential_data.credential_id
        return {"message": "Face authentication successfully registered!"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ✅ **Face Verification Route**
@app.post("/verify-face")
def verify_face(request: FaceAuthRequest):
    try:
        user_id = "user@example.com"
        credential_id = users_db.get(user_id)

        if not credential_id:
            raise HTTPException(status_code=401, detail="No registration found")

        verify_authentication_response(
            credential=request.credential,
            expected_challenge="123456",
            expected_rp_id="ai-auth.onrender.com",
            credential_id=credential_id
        )

        # ✅ Generate JWT token
        token = generate_jwt(user_id)
        return {"message": "Face verification successful!", "token": token}

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# ✅ **JWT Token Generation**
def generate_jwt(email: str):
    expiration = datetime.utcnow() + timedelta(hours=2)
    payload = {"sub": email, "exp": expiration}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# ✅ **Protected Route**
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

# ✅ **Root Route (`/`) for Health Checks**
from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def home():
    return "<h1>AI Authentication API is Live 🚀</h1>"

# ✅ **Correcte Poortbinding voor Render**
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Render geeft de poort via de omgevingsvariabele
    uvicorn.run(app, host="0.0.0.0", port=port)
