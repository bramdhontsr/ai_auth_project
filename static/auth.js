// ✅ **1️⃣ REGISTRATIE VAN GEZICHTSHERKENNING**
async function registerFace() {
    let publicKey = {
        challenge: new Uint8Array(32),
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
async function fetchChallenge() {
    let response = await fetch("/generate-challenge");
    let data = await response.json();
    return data.challenge;
}

    try {
        let credential = await navigator.credentials.create({ publicKey });

        let response = await fetch("https://ai-auth.onrender.com/register-face", { // ⬅️ Gebruik de volledige URL
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
    let publicKey = {
        challenge: new Uint8Array(32),
        allowCredentials: [{ type: "public-key", id: new Uint8Array(16) }]
    };

    try {
        let credential = await navigator.credentials.get({ publicKey });

        let response = await fetch("https://ai-auth.onrender.com/verify-face", { // ⬅️ Gebruik de volledige URL
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
