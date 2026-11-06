
from flask import Flask, request, jsonify, render_template_string
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import ipaddress
import json
import os
import time

app = Flask(__name__)

IPAPI_KEY = os.environ.get("IPAPI_KEY")
LOCATION_CACHE = {}
CACHE_SECONDS = 6 * 60 * 60
MAX_CACHE_ENTRIES = 2000


# ==========================================
# VISITOR IP
# ==========================================

def get_visitor_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    candidate = (
        forwarded.split(",")[0].strip()
        if forwarded
        else request.remote_addr or ""
    )

    try:
        address = ipaddress.ip_address(candidate)
        return str(address) if address.is_global else None
    except ValueError:
        return None


# ==========================================
# IP GEOLOCATION
# ==========================================

def get_ip_location(ip):
    if not ip:
        return None

    cached = LOCATION_CACHE.get(ip)

    if cached and time.time() - cached["time"] < CACHE_SECONDS:
        print("Using cached IP location.")
        return cached["location"]

    params = {"q": ip}
    if IPAPI_KEY:
        params["key"] = IPAPI_KEY

    providers = [
        (
            "ipapi.is",
            "https://api.ipapi.is/?" + urlencode(params)
        ),
        (
            "ipapi.co",
            f"https://ipapi.co/{ip}/json/"
        ),
        (
            "ipwho.is",
            f"https://ipwho.is/{ip}"
        )
    ]

    for name, url in providers:
        try:
            print("Trying location provider:", name)

            req = Request(
                url,
                headers={
                    "User-Agent": "GokoLocation/1.0",
                    "Accept": "application/json"
                }
            )

            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            if data.get("error") or data.get("success") is False:
                continue

            location_data = data.get("location") or data

            result = {
                "city": data.get("city") or location_data.get("city"),
                "region": (
                    data.get("region")
                    or data.get("regionName")
                    or location_data.get("region")
                    or location_data.get("state")
                ),
                "country": (
                    data.get("country")
                    or location_data.get("country")
                ),
                "latitude": (
                    data.get("lat")
                    if data.get("lat") is not None
                    else location_data.get("latitude")
                ),
                "longitude": (
                    data.get("lon")
                    if data.get("lon") is not None
                    else location_data.get("longitude")
                ),
                "accuracy": (
                    data.get("accuracy")
                    or location_data.get("accuracy")
                )
            }

            if result["country"]:
                if len(LOCATION_CACHE) >= MAX_CACHE_ENTRIES:
                    LOCATION_CACHE.clear()

                LOCATION_CACHE[ip] = {
                    "time": time.time(),
                    "location": result
                }

                print("IP location found using:", name)
                return result

        except Exception as error:
            print(
                name,
                "failed:",
                type(error).__name__,
                str(error)[:150]
            )

    print("All IP location providers failed.")
    return None


# ==========================================
# GOKO WEBSITE
# ==========================================

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#090914">

<title>Goko — Connect with the world</title>

<style>
:root {
    --bg: #090914;
    --panel: #11111f;
    --panel-light: #18182b;
    --purple: #9b5cff;
    --purple-light: #c49aff;
    --text: #f7f4ff;
    --muted: #aaa5bd;
    --border: rgba(255,255,255,.09);
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    min-height: 100vh;
    background:
        radial-gradient(circle at 15% 15%, #32165a 0, transparent 32%),
        radial-gradient(circle at 85% 80%, #25134b 0, transparent 30%),
        var(--bg);
    color: var(--text);
    font-family: Inter, Arial, sans-serif;
    padding: 25px;
}

.navbar {
    max-width: 1320px;
    margin: 0 auto 55px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.brand {
    font-size: 30px;
    font-weight: 800;
    letter-spacing: -1.5px;
}

.brand span {
    color: var(--purple);
}

.nav-links {
    display: flex;
    align-items: center;
    gap: 30px;
    color: var(--muted);
    font-size: 14px;
}

.nav-links a {
    color: inherit;
    text-decoration: none;
}

.nav-links a:hover {
    color: white;
}

.nav-join {
    padding: 11px 20px;
    background: var(--purple);
    color: white !important;
    border-radius: 10px;
}

.main {
    max-width: 1320px;
    min-height: 690px;
    margin: auto;
    display: grid;
    grid-template-columns: 1.1fr .9fr;
    gap: 65px;
    align-items: center;
}

.hero {
    padding: 25px 0;
}

.eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 9px;
    padding: 9px 14px;
    border: 1px solid rgba(178,128,255,.3);
    background: rgba(155,92,255,.1);
    color: var(--purple-light);
    border-radius: 30px;
    font-size: 13px;
    margin-bottom: 30px;
}

.eyebrow-dot {
    width: 7px;
    height: 7px;
    background: #a879ff;
    border-radius: 50%;
}

.hero h1 {
    font-size: clamp(45px, 5.5vw, 76px);
    line-height: 1.06;
    letter-spacing: -3px;
    max-width: 700px;
}

.hero h1 span {
    color: var(--purple-light);
}

.hero-description {
    color: var(--muted);
    font-size: 18px;
    line-height: 1.8;
    max-width: 520px;
    margin-top: 25px;
}

.social-preview {
    margin-top: 45px;
    display: flex;
    align-items: center;
    gap: 18px;
    flex-wrap: wrap;
}

.avatar-stack {
    display: flex;
    padding-left: 5px;
}

.avatar {
    width: 43px;
    height: 43px;
    margin-left: -7px;
    border: 3px solid var(--bg);
    border-radius: 50%;
    display: grid;
    place-items: center;
    font-size: 20px;
    background: linear-gradient(135deg,#6845a7,#e58eb7);
}

.avatar:nth-child(2) {
    background: linear-gradient(135deg,#315c91,#8c9fe7);
}

.avatar:nth-child(3) {
    background: linear-gradient(135deg,#a75b48,#edb16b);
}

.avatar:nth-child(4) {
    background: linear-gradient(135deg,#367d70,#8ac8b4);
}

.social-caption {
    color: var(--muted);
    font-size: 13px;
    line-height: 1.6;
}

.social-caption strong {
    color: white;
    display: block;
}

.visual {
    margin-top: 50px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 17px;
    max-width: 560px;
}

.visual-card {
    min-height: 155px;
    border-radius: 22px;
    padding: 22px;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    box-shadow: 0 15px 50px #0005;
    overflow: hidden;
}

.visual-card:first-child {
    background: linear-gradient(145deg,#6b398e,#d77c9d,#3c376f);
}

.visual-card:last-child {
    background: linear-gradient(145deg,#1c5375,#6975c2,#b17bc5);
    transform: translateY(22px);
}

.visual-card .emoji {
    font-size: 36px;
    margin-bottom: 12px;
}

.visual-card strong {
    font-size: 16px;
}

.visual-card small {
    color: #eee5ff;
    margin-top: 5px;
}

.login-area {
    display: flex;
    justify-content: center;
}

.login-card {
    width: 100%;
    max-width: 470px;
    padding: 42px;
    border: 1px solid var(--border);
    border-radius: 25px;
    background: rgba(17,17,31,.94);
    box-shadow: 0 25px 90px rgba(0,0,0,.35);
}

.login-card h2 {
    font-size: 29px;
    letter-spacing: -.7px;
}

.login-subtitle {
    color: var(--muted);
    margin-top: 10px;
    margin-bottom: 32px;
    font-size: 14px;
}

.field {
    margin-bottom: 18px;
}

.field label {
    display: block;
    font-size: 13px;
    color: #d8d2e8;
    margin-bottom: 9px;
}

.field input {
    width: 100%;
    height: 52px;
    padding: 0 15px;
    color: white;
    background: #0c0c18;
    border: 1px solid #343248;
    border-radius: 11px;
    font-size: 15px;
    outline: none;
}

.field input:focus {
    border-color: var(--purple);
    box-shadow: 0 0 0 3px rgba(155,92,255,.12);
}

.field input::placeholder {
    color: #777287;
}

.form-options {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: var(--muted);
    font-size: 12px;
    margin: 5px 0 22px;
}

.form-options a {
    color: var(--purple-light);
    text-decoration: none;
}

.login-button {
    width: 100%;
    height: 53px;
    border: none;
    border-radius: 11px;
    background: linear-gradient(100deg,#9b5cff,#7042e5);
    color: white;
    font-size: 16px;
    font-weight: 700;
    cursor: pointer;
    transition: .2s;
}

.login-button:hover {
    filter: brightness(1.15);
    transform: translateY(-1px);
}

.divider {
    display: flex;
    align-items: center;
    gap: 13px;
    color: #777287;
    font-size: 12px;
    margin: 25px 0;
}

.divider::before,
.divider::after {
    content: "";
    height: 1px;
    flex: 1;
    background: var(--border);
}

.create-account {
    text-align: center;
    color: var(--muted);
    font-size: 13px;
}

.create-account a {
    color: var(--purple-light);
    text-decoration: none;
    font-weight: 700;
}

#loginStatus {
    min-height: 18px;
    margin-top: 15px;
    text-align: center;
    color: var(--purple-light);
    font-size: 12px;
    line-height: 1.5;
}

.location-note {
    margin-top: 27px;
    padding: 15px;
    background: rgba(155,92,255,.07);
    border: 1px solid rgba(155,92,255,.18);
    border-radius: 13px;
}

.location-note h3 {
    font-size: 13px;
    color: var(--purple-light);
    margin-bottom: 7px;
}

.location-note p {
    color: var(--muted);
    font-size: 11px;
    line-height: 1.6;
}

#locationStatus {
    margin-top: 8px;
    color: #c6a6ff;
    overflow-wrap: anywhere;
}

.footer {
    max-width: 1320px;
    margin: 65px auto 10px;
    padding-top: 20px;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    color: #777287;
    font-size: 12px;
}

@media(max-width: 950px) {
    .main {
        grid-template-columns: 1fr;
        gap: 35px;
    }

    .hero {
        text-align: center;
    }

    .hero-description,
    .visual {
        margin-left: auto;
        margin-right: auto;
    }

    .social-preview {
        justify-content: center;
    }

    .login-card {
        max-width: 550px;
    }

    .visual-card:last-child {
        transform: none;
    }
}

@media(max-width: 600px) {
    body {
        padding: 18px;
    }

    .navbar {
        margin-bottom: 25px;
    }

    .brand {
        font-size: 26px;
    }

    .nav-links a:not(.nav-join) {
        display: none;
    }

    .hero h1 {
        font-size: 46px;
        letter-spacing: -2px;
    }

    .hero-description {
        font-size: 15px;
    }

    .visual-card {
        min-height: 130px;
        padding: 15px;
    }

    .login-card {
        padding: 28px 22px;
    }

    .login-card h2 {
        font-size: 25px;
    }

    .footer {
        flex-direction: column;
        gap: 10px;
        text-align: center;
    }
}
</style>
</head>

<body>

<header class="navbar">
    <div class="brand">Goko<span>.</span></div>

    <nav class="nav-links">
        <a href="#about">About</a>
        <a href="#features">Discover</a>
        <a href="#signin" class="nav-join">Sign in</a>
    </nav>
</header>

<main class="main">

    <section class="hero" id="about">

        <div class="eyebrow">
            <span class="eyebrow-dot"></span>
            YOUR WORLD. YOUR PEOPLE.
        </div>

        <h1>
            Make every
            connection
            <span>count.</span>
        </h1>

        <p class="hero-description">
            Discover new perspectives, share the moments that matter,
            and stay connected with the people who make your world
            interesting.
        </p>

        <div class="social-preview">
            <div class="avatar-stack">
                <div class="avatar">😊</div>
                <div class="avatar">🌿</div>
                <div class="avatar">✨</div>
                <div class="avatar">🌊</div>
            </div>

            <div class="social-caption">
                <strong>A place for everyone</strong>
                Discover people and ideas from everywhere.
            </div>
        </div>

        <div class="visual" id="features">
            <div class="visual-card">
                <span class="emoji">🌆</span>
                <strong>Share your moments</strong>
                <small>Every story has a place.</small>
            </div>

            <div class="visual-card">
                <span class="emoji">🌍</span>
                <strong>Explore the world</strong>
                <small>Find something new every day.</small>
            </div>
        </div>

    </section>

    <section class="login-area" id="signin">

        <div class="login-card">

            <h2>Welcome back</h2>

            <p class="login-subtitle">
                Sign in to continue to your Goko experience.
            </p>

            <form id="loginForm">

                <div class="field">
                    <label for="email">Email address</label>
                    <input
                        id="email"
                        name="email"
                        type="email"
                        placeholder="you@example.com"
                        autocomplete="username"
                        required
                        maxlength="120">
                </div>

                <div class="field">
                    <label for="password">Password</label>
                    <input
                        id="password"
                        name="password"
                        type="password"
                        placeholder="Enter your password"
                        autocomplete="current-password"
                        required
                        maxlength="128">
                </div>

                <div class="form-options">
                    <span>Secure sign-in experience</span>
                    <a href="#signin" id="forgotLink">Forgot password?</a>
                </div>

                <button class="login-button" type="submit">
                    Sign in
                </button>

                <p id="loginStatus" aria-live="polite"></p>

            </form>

            <div class="divider">OR</div>

            <p class="create-account">
                New to Goko?
                <a href="#signin" id="createLink">Create an account</a>
            </p>

            <div class="location-note">
                <h3>📍 Location services</h3>

                <p>
                    Goko can estimate your general location from your
                    connection IP. It may also request your device
                    location when this page opens. Your browser controls
                    permission, and precise coordinates are sent only
                    when you allow access.
                </p>

                <p id="locationStatus" aria-live="polite">
                    Checking location availability...
                </p>
            </div>

        </div>

    </section>

</main>

<footer class="footer">
    <span>© 2026 Goko. All rights reserved.</span>
    <span>Connect with the world.</span>
</footer>

<script>
const loginForm = document.getElementById("loginForm");
const loginStatus = document.getElementById("loginStatus");

loginForm.addEventListener("submit", function(event) {
    event.preventDefault();

    // Authentication is not enabled yet.
    // Do not send or store the entered credentials.
    loginStatus.textContent =
        "Account sign-in is not available yet. Please check back soon.";

    loginForm.reset();
});

document.getElementById("forgotLink").addEventListener("click", function(event) {
    event.preventDefault();
    loginStatus.textContent =
        "Password recovery will be available when accounts are enabled.";
});

document.getElementById("createLink").addEventListener("click", function(event) {
    event.preventDefault();
    loginStatus.textContent =
        "Account registration is coming soon.";
});


// ==========================================
// AUTOMATIC DEVICE LOCATION
// ==========================================

(function detectDeviceLocationOnLoad() {
    const status = document.getElementById("locationStatus");

    if (!navigator.geolocation) {
        status.textContent =
            "Device location is unavailable. Approximate IP location may be used.";
        return;
    }

    status.textContent =
        "Checking device location. Your browser may ask for permission.";

    navigator.geolocation.getCurrentPosition(
        async function(position) {
            const latitude = position.coords.latitude;
            const longitude = position.coords.longitude;
            const accuracy = position.coords.accuracy;

            status.textContent =
                "Device location received. Reported accuracy: " +
                Math.round(accuracy) + " metres.";

            try {
                const response = await fetch("/api/location", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        latitude: latitude,
                        longitude: longitude,
                        accuracy: accuracy
                    })
                });

                if (!response.ok) {
                    throw new Error("Location request failed.");
                }

            } catch (error) {
                status.textContent =
                    "Location was obtained but could not be sent. " +
                    "Approximate IP location may still be available.";

                console.error(error);
            }
        },

        function(error) {
            if (error.code === error.PERMISSION_DENIED) {
                status.textContent =
                    "Device location permission was denied. " +
                    "Approximate IP location may be used.";
            } else if (error.code === error.TIMEOUT) {
                status.textContent =
                    "Device location timed out. Approximate IP location may be used.";
            } else {
                status.textContent =
                    "Device location is unavailable. Approximate IP location may be used.";
            }
        },

        {
            enableHighAccuracy: true,
            timeout: 30000,
            maximumAge: 0
        }
    );
})();
</script>

</body>
</html>
"""


# ==========================================
# HOME PAGE
# ==========================================

@app.get("/")
def home():
    visitor_ip = get_visitor_ip()

    print("\n--- GOKO VISITOR ---")

    if not visitor_ip:
        print("Public visitor IP unavailable.")
        print("--------------------\n")
        return render_template_string(HTML)

    print("Public visitor IP received.")

    location = get_ip_location(visitor_ip)

    if location:
        print("Approximate city:", location["city"])
        print("Region:", location["region"])
        print("Country:", location["country"])
        print(
            "Approximate coordinates:",
            location["latitude"],
            location["longitude"]
        )
        print("Provider accuracy:", location["accuracy"])
    else:
        print("IP geolocation unavailable.")

    print("--------------------\n")

    return render_template_string(HTML)


# ==========================================
# DEVICE LOCATION ENDPOINT
# ==========================================

@app.post("/api/location")
def receive_location():
    data = request.get_json(silent=True) or {}

    try:
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])
        accuracy = float(data["accuracy"])
    except (KeyError, TypeError, ValueError):
        return jsonify(error="Invalid location data"), 400

    if not (
        -90 <= latitude <= 90
        and -180 <= longitude <= 180
        and 0 <= accuracy <= 100000
    ):
        return jsonify(error="Location values out of range"), 400

    # Received only after browser permission is granted.
    # Coordinates are logged for this request, not saved persistently.
    print("\n--- GOKO DEVICE LOCATION ---")
    print(f"Latitude: {latitude:.6f}")
    print(f"Longitude: {longitude:.6f}")
    print(f"Reported accuracy: {accuracy:.0f} metres")
    print("----------------------------\n")

    return jsonify(status="received")


# ==========================================
# LOCAL DEVELOPMENT
# ==========================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
