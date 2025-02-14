// ✅ **1️⃣ REGISTRATIE VAN GEZICHTSHERKENNING**
async function registerFace() {
    try {
        // Haal een unieke challenge op van de server
        let challenge = await fetchChallenge();

        let publicKey = {
            challenge: Uint8Array.from(atob(challenge), c => c.charCodeAt(0)), // Converteer challenge correct
            rp: { name: "https://thepraxisofeverything.com" },
            user: {
                id: new Uint8Array(16),
                name: "gebruiker@example.com",
                displayName: "Gebruiker",
            },
            pubKeyCredParams: [{ type: "public-key", alg: -7 }],
            authenticatorSelection: { authenticatorAttachment: "platform" },
            timeout: 60000,
            attestation: "direct",
        };

        let credential = await navigator.credentials.create({ publicKey });

        let response = await fetch("/register-face", { // Correcte API-aanroep
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ credential: credential.response })
        });

        let data = await response.json();
        if (response.ok) {
            alert("Gezichtsherkenning succesvol geregistreerd!");
        } else {
            alert("Registratie mislukt: " + data.detail);
        }
    } catch (error) {
        console.error("Registratie mislukt", error);
        alert("Registratie mislukt. Probeer opnieuw.");
    }
}

// ✅ **2️⃣ INLOGGEN MET GEZICHTSHERKENNING**
async function loginWithFace() {
    try {
        // Haal een unieke challenge op van de server
        let challenge = await fetchChallenge();

        let publicKey = {
            challenge: Uint8Array.from(atob(challenge), c => c.charCodeAt(0)), // Correcte challenge
            allowCredentials: [{ type: "public-key", id: new Uint8Array(16) }]
        };

        let credential = await navigator.credentials.get({ publicKey });

        let response = await fetch("/verify-face", { // Correcte API-aanroep
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ credential: credential.response })
        });

        let data = await response.json();
        if (response.ok) {
            localStorage.setItem("token", data.token); // Token opslaan
            window.location.href = "/dashboard.html"; // Doorsturen naar beveiligde pagina
        } else {
            alert("Gezichtsverificatie mislukt");
        }
    } catch (error) {
        console.error("Verificatie mislukt", error);
        alert("Verificatie mislukt. Probeer opnieuw.");
    }
}

// ✅ **3️⃣ CHALLENGE OPHALEN**
async function fetchChallenge() {
    try {
        let response = await fetch("/generate-challenge");
        let data = await response.json();
        return data.challenge;
    } catch (error) {
        console.error("Fout bij ophalen van challenge:", error);
        alert("Kan challenge niet ophalen, probeer later opnieuw.");
        throw error;
    }
}
