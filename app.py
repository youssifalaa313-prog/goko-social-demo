
from flask import Flask, request, jsonify, render_template_string
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import ipaddress
import json
import os
import time

app = Flask(__name__)

# Optional API key configured in Render Environment Variables.
IPAPI_KEY = os.environ.get("IPAPI_KEY")

# Temporary memory cache.
LOCATION_CACHE = {}
CACHE_SECONDS = 6 * 60 * 60
MAX_CACHE_ENTRIES = 2000


# ==========================================
# VISITOR IP EXTRACTION
# ==========================================

def get_visitor_ip():
    """
    Render forwards the original visitor IP in
    the X-Forwarded-For header.

    This deployment assumes Render's documented
    proxy header format.
    """

    forwarded = request.headers.get("X-Forwarded-For", "")

    if forwarded:
        candidate = forwarded.split(",")[0].strip()
    else:
        candidate = request.remote_addr or ""

    try:
        address = ipaddress.ip_address(candidate)

        if not address.is_global:
            print("Visitor IP is not public.")
            return None

        return str(address)

    except ValueError:
        print("Invalid visitor IP received.")
        return None


# ==========================================
# IP GEOLOCATION
# ==========================================

def get_ip_location(ip):

    if not ip:
        return None

    cached = LOCATION_CACHE.get(ip)

    if cached and time.time() - cached["time"] < CACHE_SECONDS:
        print("Using cached location.")
        return cached["location"]

    providers = []

    # Provider 1: ipapi.is
    params = {"q": ip}

    if IPAPI_KEY:
        params["key"] = IPAPI_KEY

    providers.append({
        "name": "ipapi.is",
        "url": "https://api.ipapi.is/?" + urlencode(params)
    })

    # Provider 2: ipapi.co
    providers.append({
        "name": "ipapi.co",
        "url": f"https://ipapi.co/{ip}/json/"
    })

    # Provider 3: ipwho.is
    providers.append({
        "name": "ipwho.is",
        "url": f"https://ipwho.is/{ip}"
    })

    for provider in providers:

        try:
            print("Trying provider:", provider["name"])

            req = Request(
                provider["url"],
                headers={
                    "User-Agent": "GokoLocationDemo/1.0",
                    "Accept": "application/json"
                }
            )

            with urlopen(req, timeout=10) as response:
                data = json.loads(
                    response.read().decode("utf-8")
                )

            if data.get("error") or data.get("success") is False:
                print("Provider returned an error.")
                continue

            location_data = data.get("location") or data

            result = {
                "city": (
                    data.get("city")
                    or location_data.get("city")
                ),
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

                print("Geolocation succeeded:", provider["name"])

                return result

            print("No usable location returned.")

        except Exception as error:

            print(
                provider["name"],
                "failed:",
                type(error).__name__,
                str(error)[:200]
            )

    print("All geolocation providers failed.")
    return None


# ==========================================
# GOKO HTML AND CSS
# ==========================================

HTML = r"""
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>Goko.com</title>

<style>

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    min-height: 100vh;
    padding: 30px;
    color: white;
    font-family: Arial, sans-serif;

    background:
        radial-gradient(
            ellipse at 10% 90%,
            #38116d,
            transparent 40%
        ),
        radial-gradient(
            ellipse at 90% 10%,
            #211052,
            transparent 40%
        ),
        #080a18;

    display: flex;
    align-items: center;
    justify-content: center;
}

.container {
    width: 100%;
    max-width: 1400px;
    min-height: 780px;

    display: grid;
    grid-template-columns: 1fr 1.05fr;

    border: 1px solid #30245b;
    border-radius: 35px;

    background: rgba(12, 13, 32, .95);
    overflow: hidden;
}

.left {
    padding: 65px 70px;
    display: flex;
    flex-direction: column;
}

.logo {
    font-size: 43px;
    font-weight: 800;
    letter-spacing: -2px;
}

.purple,
.logo span {
    color: #a855f7;
}

.logo-symbol {
    font-size: 55px;
    margin-right: 12px;
    vertical-align: middle;
}

.intro {
    margin-top: 55px;
}

.intro h1 {
    font-size: clamp(38px, 4vw, 55px);
    line-height: 1.12;
    margin-bottom: 22px;
}

.intro p {
    color: #b9b9d0;
    font-size: 19px;
    line-height: 1.7;
    max-width: 480px;
}

.visual {
    margin-top: 45px;
    min-height: 230px;

    display: flex;
    align-items: center;
    justify-content: center;
    gap: 14px;
}

.photo {
    width: 165px;
    height: 190px;

    border-radius: 20px;
    border: 3px solid #b68aff;

    display: flex;
    justify-content: center;
    align-items: center;

    font-size: 55px;

    background:
        linear-gradient(
            145deg,
            #552c9e,
            #ed769b,
            #22265a
        );

    transform: rotate(-8deg);
    box-shadow: 0 12px 40px #0008;
}

.photo.second {
    height: 155px;
    transform: rotate(8deg);

    background:
        linear-gradient(
            145deg,
            #152d63,
            #7862c8,
            #ba77d2
        );
}

.features {
    margin-top: auto;
    padding-top: 35px;

    display: flex;
    justify-content: space-between;
    gap: 10px;
}

.feature {
    text-align: center;
    flex: 1;
}

.feature div {
    font-size: 30px;
    color: #b88aff;
    margin-bottom: 12px;
}

.feature p {
    font-size: 14px;
}

.right {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 45px;
}

.login-card {
    width: 100%;
    max-width: 590px;
    padding: 55px 50px;

    border: 1px solid #292944;
    border-radius: 30px;

    background:
        linear-gradient(
            145deg,
            #121426,
            #0d0e1c
        );
}

.login-card h2 {
    text-align: center;
    font-size: 35px;
    margin-bottom: 12px;
}

.subtitle {
    text-align: center;
    color: #b8b8cc;
    margin-bottom: 42px;
}

.field {
    margin-bottom: 20px;
}

.field input {
    width: 100%;
    padding: 20px;

    background: #111322;
    border: 1px solid #41405d;
    border-radius: 15px;

    color: white;
    font-size: 16px;
    outline: none;
}

.field input:focus {
    border-color: #a855f7;
}

.login-button,
.location-button {
    width: 100%;
    padding: 19px;

    border: 0;
    border-radius: 14px;

    background:
        linear-gradient(
            90deg,
            #9333ea,
            #6334e9
        );

    color: white;
    font-size: 18px;
    font-weight: bold;
    cursor: pointer;
    margin-top: 12px;
}

.login-button:hover,
.location-button:hover {
    filter: brightness(1.15);
}

.signup {
    text-align: center;
    color: #b9b9cc;
    margin-top: 35px;
}

.location-card {
    margin-top: 35px;
    padding: 25px;

    border: 1px solid #6334e9;
    border-radius: 20px;

    background: #111322;
    text-align: center;
}

.location-card h3 {
    color: #c084fc;
    margin-bottom: 10px;
}

.location-card p {
    color: #b9b9cc;
    font-size: 14px;
    line-height: 1.6;
}

#locationStatus {
    margin-top: 15px;
    color: #c084fc;
    overflow-wrap: anywhere;
}

@media(max-width:900px) {

    body {
        padding: 15px;
    }

    .container {
        grid-template-columns: 1fr;
    }

    .left {
        padding: 35px;
    }

    .intro {
        margin-top: 35px;
    }

    .visual {
        min-height: 180px;
    }

    .features {
        margin-top: 30px;
    }

    .right {
        padding: 20px;
    }

    .login-card {
        padding: 40px 25px;
    }
}

@media(max-width:480px) {

    .left {
        padding: 25px;
    }

    .logo {
        font-size: 34px;
    }

    .intro h1 {
        font-size: 36px;
    }

    .photo {
        width: 125px;
        height: 145px;
    }

    .photo.second {
        height: 120px;
    }
}

</style>

</head>

<body>

<div class="container">

<section class="left">

    <div class="logo">
        <span class="logo-symbol">G</span>
        Goko<span>.com</span>
    </div>

    <div class="intro">

        <h1>
            Connect, Share,<br>
            Explore on <span class="purple">Goko</span>
        </h1>

        <p>
            A social space to share your moments,
            follow what you love, and stay connected
            with your friends.
        </p>

    </div>

    <div class="visual">

        <div class="photo">🌆</div>
        <div class="photo second">🏔️</div>

    </div>

    <div class="features">

        <div class="feature">
            <div>♧</div>
            <p>Meet People</p>
        </div>

        <div class="feature">
            <div>▧</div>
            <p>Share Posts</p>
        </div>

        <div class="feature">
            <div>◎</div>
            <p>Discover More</p>
        </div>

    </div>

</section>

<section class="right">

<div class="login-card">

    <h2>
        Welcome to <span class="purple">Goko.com</span>
    </h2>

    <p class="subtitle">
        Explore your social space
    </p>

    <form id="demoForm">

        <div class="field">

            <input
                name="username"
                placeholder="Demo username"
                required
                maxlength="40">

        </div>

        <div class="field">

            <input
                name="password"
                type="password"
                placeholder="Demo password"
                required
                maxlength="40">

        </div>

        <button class="login-button" type="submit">
            Try Demo Login
        </button>

    </form>

    <p id="loginStatus"
       class="subtitle"
       style="margin:15px 0 0"></p>

    <div class="signup">
        Goko security demonstration
    </div>

    <div class="location-card">

        <h3>📍 Goko Location Finder</h3>

        <p>
            Goko estimates your general location from
            your connection IP when you visit.
            This is approximate, not precise GPS.
        </p>

        <p id="locationStatus" aria-live="polite">
            Approximate location lookup happens when this page loads.
        </p>

        <button
            class="location-button"
            id="shareLocation">

            Share My GPS Location (Optional)

        </button>

    </div>

</div>

</section>

</div>

<script>

document.getElementById("demoForm")
.addEventListener("submit", e => {

    e.preventDefault();

    document.getElementById("loginStatus").textContent =
        "This is a demo page. No password was sent or stored.";

    e.target.reset();

});

document.getElementById("shareLocation")
.addEventListener("click", () => {

    const status = document.getElementById("locationStatus");

    if (!navigator.geolocation) {
        status.textContent =
            "Geolocation is not supported by this browser.";
        return;
    }

    status.textContent = "Waiting for your permission...";

    navigator.geolocation.getCurrentPosition(
        async pos => {

            const {
                latitude,
                longitude,
                accuracy
            } = pos.coords;

            try {

                const response = await fetch("/api/location", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        latitude,
                        longitude,
                        accuracy
                    })
                });

                if (!response.ok) {
                    throw new Error("Request failed");
                }

                status.textContent =
                    "Your GPS location was shared with the Goko demo server.";

            } catch (error) {

                status.textContent =
                    "Server could not receive the location.";

            }

        },

        error => {

            status.textContent =
                "Location not shared: " + error.message;

        },

        {
            enableHighAccuracy: true,
            timeout: 15000
        }
    );

});

</script>

</body>
</html>
"""


# ==========================================
# HOME ROUTE
# ==========================================

@app.get("/")
def home():

    visitor_ip = get_visitor_ip()

    if not visitor_ip:
        print("GOKO: Visitor IP unavailable.")
        return render_template_string(HTML)

    print("\n--- GOKO VISITOR LOOKUP ---")
    print("Public visitor IP received.")

    location = get_ip_location(visitor_ip)

    if location:

        print("City:", location["city"])
        print("Region:", location["region"])
        print("Country:", location["country"])

        print(
            "Approximate coordinates:",
            location["latitude"],
            location["longitude"]
        )

        print("Accuracy:", location["accuracy"])

        print("---------------------------\n")

    else:

        print("No usable geolocation result.")
        print("---------------------------\n")

    return render_template_string(HTML)


# ==========================================
# OPTIONAL GPS ENDPOINT
# ==========================================

@app.post("/api/location")
def receive_location():

    data = request.get_json(silent=True) or {}

    try:

        lat = float(data["latitude"])
        lon = float(data["longitude"])
        accuracy = float(data["accuracy"])

    except (KeyError, TypeError, ValueError):

        return jsonify(error="Invalid location data"), 400

    if not (
        -90 <= lat <= 90
        and -180 <= lon <= 180
        and 0 <= accuracy <= 100000
    ):

        return jsonify(error="Location values out of range"), 400

    # Only acknowledge voluntary GPS sharing.
    # Do not retain visitor coordinates.

    print(
        "Consent-based GPS location received; "
        f"accuracy={accuracy:.0f} m"
    )

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
