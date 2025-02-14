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


port = int(os.getenv("PORT", "8000"))  # Get PORT from Render, default to 8000

if __name__ == "__main__":
    print(f"Starting server on port {port}...")  # Debugging line
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)


# Initialize FastAPI app
app = FastAPI()
security = HTTPBearer()

# ✅ **JWT Configuration**
SECRET_KEY = os.environ.get("SECRET_KEY", "your_secret_key")  # Haal secret uit de omgeving voor veiligheid
ALGORITHM = "HS256"

# ✅ **In-memory database voor face authentication**
users_db: Dict[str, str] = {}
challenges: Dict[str, str] = {}  # Opslag van gegenereerde challenges per gebruiker

# ✅ **Pydantic model voor WebAuthn authenticatie**
class FaceAuthRequest(BaseModel):
    credential: dict

# ✅ **1️⃣ Face Registration Route**
@app.post("/register-face")
def register_face(request: FaceAuthRequest):
    try:
        user_id = "user@example.com"
        expected_challenge = challenges.get(user_id)

        if not expected_challenge:
            raise HTTPException(status_code=400, detail="Geen challenge gevonden voor deze gebruiker")

        credential_data = verify_registration_response(
            credential=request.credential,
            expected_challenge=expected_challenge,
            expected_rp_id="ai-auth.onrender.com"
        )

        # ✅ Opslaan van gebruiker en credential ID
        users_db[user_id] = credential_data.credential_id
        return {"message": "Face authentication succesvol geregistreerd!"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ✅ **2️⃣ Face Verification Route**
@app.post("/verify-face")
def verify_face(request: FaceAuthRequest):
    try:
        user_id = "user@example.com"
        credential_id = users_db.get(user_id)

        if not credential_id:
            raise HTTPException(status_code=401, detail="Geen registratie gevonden")

        expected_challenge = challenges.get(user_id)
        if not expected_challenge:
            raise HTTPException(status_code=401, detail="Geen challenge gevonden voor deze gebruiker")

        verify_authentication_response(
            credential=request.credential,
            expected_challenge=expected_challenge,
            expected_rp_id="ai-auth.onrender.com",
            credential_id=credential_id
        )

        # ✅ Verwijder de gebruikte challenge
        del challenges[user_id]

        # ✅ Genereer JWT-token
        token = generate_jwt(user_id)
        return {"message": "Face verification succesvol!", "token": token}

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
    challenge = secrets.token_urlsafe(32)  # Veilige willekeurige challenge
    challenges[user_id] = challenge
    return {"challenge": challenge}

# ✅ **5️⃣ Protected Route**
@app.get("/protected")
def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"message": "Toegang verleend!", "user": payload["sub"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token is verlopen")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Ongeldig token")

# ✅ **6️⃣ Health Check Route voor Render**
from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def home():
    return "<h1>AI Authentication API is Live 🚀</h1>"

