
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Goko.com</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{
 min-height:100vh;padding:30px;color:white;font-family:Arial,sans-serif;
 background:radial-gradient(ellipse at 10% 90%,#38116d,transparent 40%),
 radial-gradient(ellipse at 90% 10%,#211052,transparent 40%),#080a18;
 display:flex;align-items:center;justify-content:center
}
.container{
 width:100%;max-width:1400px;min-height:780px;
 display:grid;grid-template-columns:1fr 1.05fr;
 border:1px solid #30245b;border-radius:35px;
 background:rgba(12,13,32,.95);overflow:hidden
}
.left{padding:65px 70px;display:flex;flex-direction:column}
.logo{font-size:43px;font-weight:800;letter-spacing:-2px}
.purple,.logo span{color:#a855f7}
.logo-symbol{font-size:55px;margin-right:12px;vertical-align:middle}
.intro{margin-top:55px}
.intro h1{font-size:clamp(38px,4vw,55px);line-height:1.12;margin-bottom:22px}
.intro p{color:#b9b9d0;font-size:19px;line-height:1.7;max-width:480px}
.visual{margin-top:45px;min-height:230px;display:flex;align-items:center;justify-content:center;gap:14px}
.photo{
 width:165px;height:190px;border-radius:20px;border:3px solid #b68aff;
 display:flex;justify-content:center;align-items:center;font-size:55px;
 background:linear-gradient(145deg,#552c9e,#ed769b,#22265a);
 transform:rotate(-8deg);box-shadow:0 12px 40px #0008
}
.photo.second{height:155px;transform:rotate(8deg);background:linear-gradient(145deg,#152d63,#7862c8,#ba77d2)}
.features{margin-top:auto;padding-top:35px;display:flex;justify-content:space-between;gap:10px}
.feature{text-align:center;flex:1}
.feature div{font-size:30px;color:#b88aff;margin-bottom:12px}
.feature p{font-size:14px}
.right{display:flex;align-items:center;justify-content:center;padding:45px}
.login-card{
 width:100%;max-width:590px;padding:55px 50px;
 border:1px solid #292944;border-radius:30px;
 background:linear-gradient(145deg,#121426,#0d0e1c)
}
.login-card h2{text-align:center;font-size:35px;margin-bottom:12px}
.subtitle{text-align:center;color:#b8b8cc;margin-bottom:42px}
.field{margin-bottom:20px}
.field input{
 width:100%;padding:20px;background:#111322;border:1px solid #41405d;
 border-radius:15px;color:white;font-size:16px;outline:none
}
.field input:focus{border-color:#a855f7}
.login-button,.location-button{
 width:100%;padding:19px;border:0;border-radius:14px;
 background:linear-gradient(90deg,#9333ea,#6334e9);
 color:white;font-size:18px;font-weight:bold;cursor:pointer;margin-top:12px
}
.login-button:hover,.location-button:hover{filter:brightness(1.15)}
.options{display:flex;justify-content:space-between;margin-top:24px;color:#c5c5d5;font-size:14px}
.options a,.signup a{color:#c084fc;text-decoration:none}
.signup{text-align:center;color:#b9b9cc;margin-top:35px}
.location-card{
 margin-top:35px;padding:25px;border:1px solid #6334e9;
 border-radius:20px;background:#111322;text-align:center
}
.location-card h3{color:#c084fc;margin-bottom:10px}
.location-card p{color:#b9b9cc;font-size:14px;line-height:1.6}
#locationStatus{margin-top:15px;color:#c084fc;overflow-wrap:anywhere}
@media(max-width:900px){
 body{padding:15px}.container{grid-template-columns:1fr}
 .left{padding:35px}.intro{margin-top:35px}
 .visual{min-height:180px}.features{margin-top:30px}
 .right{padding:20px}.login-card{padding:40px 25px}
}
@media(max-width:480px){
 .left{padding:25px}.logo{font-size:34px}
 .intro h1{font-size:36px}.photo{width:125px;height:145px}
 .photo.second{height:120px}
}
</style>
</head>
<body>
<div class="container">
<section class="left">
 <div class="logo"><span class="logo-symbol">G</span>Goko<span>.com</span></div>
 <div class="intro">
  <h1>Connect, Share,<br>Explore on <span class="purple">Goko</span></h1>
  <p>A social space to share your moments, follow what you love, and stay connected with your friends.</p>
 </div>
 <div class="visual"><div class="photo">🌆</div><div class="photo second">🏔️</div></div>
 <div class="features">
  <div class="feature"><div>♧</div><p>Meet People</p></div>
  <div class="feature"><div>▧</div><p>Share Posts</p></div>
  <div class="feature"><div>◎</div><p>Discover More</p></div>
 </div>
</section>
<section class="right">
<div class="login-card">
 <h2>Welcome to <span class="purple">Goko.com</span></h2>
 <p class="subtitle">Explore your social space</p>

 <form id="demoForm">
  <div class="field"><input name="username" placeholder="Demo username" required maxlength="40"></div>
  <div class="field"><input name="password" type="password" placeholder="Demo password" required maxlength="40"></div>
  <button class="login-button" type="submit">Try Demo Login</button>
 </form>
 <p id="loginStatus" class="subtitle" style="margin:15px 0 0"></p>

 <div class="signup">Goko security demonstration</div>

 <div class="location-card">
  <h3>📍 Goko Location Finder</h3>
  <p>Your location is only shared after you press the button and approve your browser's permission request.</p>
  <button class="location-button" id="shareLocation">Share My GPS Location</button>
  <p id="locationStatus" aria-live="polite">Location has not been shared.</p>
 </div>
</div>
</section>
</div>
<script>
document.getElementById("demoForm").addEventListener("submit", async e => {
 e.preventDefault();
 const status = document.getElementById("loginStatus");
 status.textContent = "This is a demo page. No password was sent or stored.";
 e.target.reset();
});

document.getElementById("shareLocation").addEventListener("click", () => {
 const status = document.getElementById("locationStatus");
 if (!navigator.geolocation) {
  status.textContent = "Geolocation is not supported by this browser.";
  return;
 }
 status.textContent = "Waiting for your permission...";
 navigator.geolocation.getCurrentPosition(async pos => {
  const {latitude, longitude, accuracy} = pos.coords;
  status.innerHTML = "";
  const details = document.createElement("p");
  details.textContent = `Latitude: ${latitude.toFixed(6)} | Longitude: ${longitude.toFixed(6)} | Accuracy: ${Math.round(accuracy)} m`;
  const map = document.createElement("a");
  map.href = `https://www.google.com/maps?q=${latitude},${longitude}`;
  map.target = "_blank";
  map.rel = "noopener";
  map.textContent = "Open in Google Maps";
  map.style.color = "#c084fc";
  status.append(details, map);
  try {
   const r = await fetch("/api/location", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({latitude,longitude,accuracy})
   });
   if (!r.ok) throw new Error();
   status.append(document.createTextNode(" — Shared with the Goko demo server."));
  } catch {
   status.append(document.createTextNode(" — Server could not receive the location."));
  }
 }, err => {
  status.textContent = "Location not shared: " + err.message;
 }, {enableHighAccuracy:true,timeout:15000});
});
</script>
</body>
</html>
"""

@app.get("/")
def home():
    return render_template_string(HTML)

@app.post("/api/location")
def receive_location():
    data = request.get_json(silent=True) or {}
    try:
        lat = float(data["latitude"])
        lon = float(data["longitude"])
        accuracy = float(data["accuracy"])
    except (KeyError, TypeError, ValueError):
        return jsonify(error="Invalid location data"), 400

    if not (-90 <= lat <= 90 and -180 <= lon <= 180 and 0 <= accuracy <= 100000):
        return jsonify(error="Location values out of range"), 400

    # Demonstration only: do not retain visitor coordinates.
    print(f"Consent-based location received; accuracy={accuracy:.0f} m")
    return jsonify(status="received")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
