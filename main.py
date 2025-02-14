import os
import uvicorn
import jwt
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from webauthn import verify_registration_response, verify_authentication_response
from pydantic import BaseModel
from typing import Dict
from datetime import datetime, timedelta

app = FastAPI()
security = HTTPBearer()
SECRET_KEY = "jouw_geheime_sleutel"
ALGORITHM = "HS256"

# Simpele database voor gezichtsherkenning
users_db: Dict[str, str] = {}

class FaceAuthRequest(BaseModel):
    credential: dict

# 🔹 **1️⃣ REGISTRATIE VAN GEZICHTSHERKENNING**
@app.post("/register-face")
def register_face(request: FaceAuthRequest):
    try:
        credential_data = verify_registration_response(
            request.credential,
            expected_challenge="123456",
            expected_rp_id="ai-auth.onrender.com"  # Zorg dat dit klopt met je Render-domein!
        )
        
        # Opslaan van gebruikers-ID en sleutel
        users_db["gebruiker@example.com"] = credential_data.credential_id
        return {"message": "Gezichtsherkenning succesvol geregistreerd!"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 🔹 **2️⃣ VERIFICATIE VAN GEZICHTSHERKENNING**
@app.post("/verify-face")
def verify_face(request: FaceAuthRequest):
    try:
        user_id = "gebruiker@example.com"
        credential_id = users_db.get(user_id)

        if not credential_id:
            raise HTTPException(status_code=401, detail="Geen registratie gevonden")

        verify_authentication_response(
            request.credential,
            expected_challenge="123456",
            expected_rp_id="ai-auth.onrender.com",
            credential_id=credential_id
        )

        # 🔹 JWT-token genereren
        token = generate_jwt(user_id)
        return {"message": "Gezichtsverificatie geslaagd!", "token": token}

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# 🔹 **3️⃣ JWT TOKEN GENEREREN**
def generate_jwt(email: str):
    expiration = datetime.utcnow() + timedelta(hours=2)
    payload = {"sub": email, "exp": expiration}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# 🔹 **4️⃣ BEVEILIGDE ROUTE**
@app.get("/protected")
def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"message": "Je hebt toegang!", "user": payload["sub"]}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token is verlopen")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Ongeldig token")

# Start de FastAPI server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
