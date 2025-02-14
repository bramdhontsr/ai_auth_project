async function registerUser() {
    let email = document.getElementById('email').value;
    let response = await fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
    });
    let data = await response.json();
    
    // Sla de challenge correct op in window object
    if (data.challenge) {
        window.challengeData = data.challenge;
        document.getElementById('challenge').innerText = "Challenge ontvangen: " + JSON.stringify(data.challenge);
    } else {
        document.getElementById('challenge').innerText = "Fout bij registreren";
    }
}

async function loginUser() {
    let email = document.getElementById('email').value;

    // Controleer of de challenge is opgeslagen
    if (!window.challengeData) {
        alert("Geen challenge gevonden. Registreer eerst!");
        return;
    }

    let response = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, challenge: window.challengeData })
    });

    let data = await response.json();
    
    if (response.ok) {
        document.getElementById('result').innerText = "Token: " + data.token;
    } else {
        document.getElementById('result').innerText = "Verificatie mislukt: " + data.detail;
    }
}
