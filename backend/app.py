from flask import Flask, request, jsonify, render_template, redirect
import secrets
import requests


import time, jwt, os
def generate_join_token(username, room_name):
    now = int(time.time())
    payload = {
        "iss": os.environ["LIVEKIT_API_KEY"],
        "sub": username,
        "nbf": now,
        "exp": now + 3600,  # valid for 1 hour
        "video": {"roomJoin": True, "room": room_name}
    }
    token = jwt.encode(payload, os.environ["LIVEKIT_API_SECRET"], algorithm="HS256")
    return token


LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_API_URL", "https://nothing-f9v9ildb.livekit.cloud")

app = Flask(__name__)

@app.route("/")
def main():
    return render_template("home.html")

@app.route("/create-room", methods=["POST"])
def create_room_route():
    username = request.form.get("name")
    if not username:
        return "Username is required", 400

    room_name = f"room-{secrets.token_hex(4)}"
    # Debug: Print LIVEKIT config
    print(f"[DEBUG] LIVEKIT_URL: {LIVEKIT_URL}")
    print(f"[DEBUG] LIVEKIT_API_KEY: {LIVEKIT_API_KEY}")
    masked_secret = (LIVEKIT_API_SECRET[:4] + "..." + LIVEKIT_API_SECRET[-4:]) if LIVEKIT_API_SECRET else None
    print(f"[DEBUG] LIVEKIT_API_SECRET: {masked_secret}")
    create_room(room_name)
    token = generate_join_token(username, room_name)

    # Decode join token payload for debug
    try:
        decoded_payload = jwt.decode(token, LIVEKIT_API_SECRET, algorithms=["HS256"])
        print(f"[DEBUG] Join Token Payload for user '{username}': {decoded_payload}")
    except Exception as e:
        print(f"[ERROR] Failed to decode join token: {e}")

    # Debug: Print username and room name
    print(f"[DEBUG] Username: {username}, Room Name: {room_name}")

    # Redirect user to LiveKit join URL
    join_url = f"/room?room={room_name}&token={token}"
    return redirect(join_url)

@app.route("/room")
def room():
    return render_template("room.html")

def generate_server_token():
    now = int(time.time())
    payload = {
        "iss": LIVEKIT_API_KEY,
        "nbf": now,
        "exp": now + 60,
        "video": {
            "roomCreate": True
        }
    }
    return jwt.encode(payload, LIVEKIT_API_SECRET, algorithm="HS256")

# def generate_join_token(identity, room_name):
#     now = int(time.time())
#     payload = {
#         "iss": LIVEKIT_API_KEY,
#         "sub": identity,
#         "nbf": now,
#         "exp": now + 3600,
#         "video": {
#             "roomJoin": True,
#             "room": room_name
#         }
#     }
#     # Debug: Print join token payload
#     print(f"[DEBUG] Join Token Payload to encode: {payload}")
#     return jwt.encode(payload, LIVEKIT_API_SECRET, algorithm="HS256")

def create_room(room_name):
    server_token = generate_server_token()

    # Decode server token payload for debug in create_room
    try:
        decoded_payload = jwt.decode(server_token, LIVEKIT_API_SECRET, algorithms=["HS256"])
        print(f"[DEBUG] Decoded Server Token Payload in create_room: {decoded_payload}")
    except Exception as e:
        print(f"[ERROR] Failed to decode server token in create_room: {e}")

    url = f"{LIVEKIT_URL}/twirp/livekit.RoomService/CreateRoom"
    headers = {
        "Authorization": f"Bearer {server_token}",
        "Content-Type": "application/json"
    }
    # Debug: Print the request URL and masked headers
    masked_token = str(server_token)[:8] + "..."
    debug_headers = dict(headers)
    debug_headers["Authorization"] = f"Bearer {masked_token}"
    print(f"[DEBUG] Request URL: {url}")
    print(f"[DEBUG] Request Headers: {debug_headers}")
    try:
        res = requests.post(
            url,
            headers=headers,
            json={"name": room_name}
        )
        try:
            res.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"[ERROR] Failed to create room. Status: {res.status_code}, Response: {res.text}")
            print(f"[ERROR] Exception: {e}")
            raise
        return res.json()
    except Exception as ex:
        print(f"[ERROR] Exception during create_room: {ex}")
        raise

if __name__ == "__main__":
    app.run(debug=True, port=5000)