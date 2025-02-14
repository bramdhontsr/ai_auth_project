from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
import random
from sklearn.ensemble import RandomForestClassifier
import secrets

app = FastAPI()

# Mount static files (for HTML, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Simpele database voor gebruikers en sessies
users_db = {}  # Opslag van e-mails en hun AI-authenticatie-challenge
sessions = {}  # Sessies: email -> token

# AI-authenticatie (random exponenten)
class A003558AIAuth:
    def __init__(self):
        self.period = 9
        self.modulus_13 = [pow(2, i, 13) for i in range(self.period)]
        self.modulus_21 = [pow(2, i, 21) for i in range(self.period)]
        self.secret_exponent = random.choice(self.modulus_13)
        index_in_mod13 = self.modulus_13.index(self.secret_exponent)
        self.inverse_exponent = self.modulus_21[-(index_in_mod13 + 1)]

    def generate_ai_challenge(self):
        return np.array([self.secret_exponent, self.secret_exponent * 2, self.secret_exponent * 3])

# Train AI model
X, y = [], []
for _ in range(500):
    auth_system = A003558AIAuth()
    X.append(auth_system.generate_ai_challenge())
    y.append(auth_system.inverse_exponent)

X, y = np.array(X), np.array(y)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# Beveiliging: verifieer token
def verify_token(token: str):
    for email, session_token in sessions.items():
        if session_token == token:
            return email
    raise HTTPException(status_code=401, detail="Ongeldig token")

# API: Registreren
@app.post("/register")
def register_user(email: str):
    if email in users_db:
        raise HTTPException(status_code=400, detail="Gebruiker bestaat al.")
    
    auth_system = A003558AIAuth()
    challenge = auth_system.generate_ai_challenge().tolist()
    users_db[email] = challenge
    return {"message": "Geregistreerd. Gebruik deze challenge om in te loggen.", "challenge": challenge}

# API: Inloggen
@app.post("/login")
def login_user(email: str, challenge: list[int]):
    if email not in users_db:
        raise HTTPException(status_code=400, detail="Gebruiker niet gevonden.")
    
    expected_challenge = users_db[email]
    predicted_inverse = int(model.predict([challenge])[0])
    expected_inverse = int(model.predict([expected_challenge])[0])
    
    if predicted_inverse == expected_inverse:
        session_token = secrets.token_hex(16)
        sessions[email] = session_token
        return {"message": "Inloggen gelukt.", "token": session_token}
    else:
        raise HTTPException(status_code=401, detail="Verificatie mislukt.")

# API: Dashboard ophalen
@app.get("/dashboard")
def get_dashboard(token: str):
    email = verify_token(token)
    return JSONResponse(content={"dashboard": f"Welkom, {email}! Dit is jouw persoonlijke pagina."})

# API: Web GUI serveren
@app.get("/", response_class=HTMLResponse)
def serve_gui():
    with open("static/index.html", "r") as file:
        return HTMLResponse(content=file.read())
